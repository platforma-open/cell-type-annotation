import pandas as pd
import polars as pl
import scanpy as sc
import celltypist
from celltypist import models
import argparse
import os
import numpy as np
import time
from scipy.sparse import csr_matrix

def log_message(message, status="INFO"):
    """Logs messages in a structured format."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{status}] {message}")

def load_data_long_format(file_path, gene_map_path=None):
    """
    Load long-format scRNA-seq data and convert to AnnData object.
    Optionally map Ensembl IDs to gene symbols using a mapping file.
    """
    log_message("Loading counts with Polars and Categorical optimization", "STEP")
    
    # Peek schema to handle flexible headers and identify columns for Categorical casting
    temp_scan = pl.scan_csv(file_path)
    file_schema = temp_scan.collect_schema()
    column_names = set(file_schema.keys())

    schema_overrides = {
        "Sample": pl.Categorical,
        "Ensembl Id": pl.Categorical,
        "Cell Barcode": pl.Categorical,
        "Cell ID": pl.Categorical,
        "CellId": pl.Categorical
    }
    # Only apply overrides for columns that actually exist in the file
    schema_overrides = {k: v for k, v in schema_overrides.items() if k in column_names}
    
    df_pl = pl.read_csv(file_path, schema_overrides=schema_overrides)

    # Normalize minimal expected headers
    if "Cell Barcode" not in df_pl.columns:
        if "Cell ID" in df_pl.columns:
            df_pl = df_pl.rename({"Cell ID": "Cell Barcode"})
        elif "CellId" in df_pl.columns:
            df_pl = df_pl.rename({"CellId": "Cell Barcode"})

    required_cols = {"Sample", "Cell Barcode", "Ensembl Id", "Raw gene expression"}
    if not required_cols.issubset(set(df_pl.columns)):
        missing = list(required_cols - set(df_pl.columns))
        raise ValueError(f"Input file must contain columns: {required_cols}. Missing: {missing}")

    # Map Ensembl IDs to gene symbols if provided
    if gene_map_path:
        log_message(f"Mapping Ensembl IDs to gene symbols from {gene_map_path}", "STEP")
        gene_map = pl.read_csv(gene_map_path).select(["Ensembl Id", "Gene symbol"]).unique()
        # Cast mapping columns to categorical to match main dataframe
        gene_map = gene_map.with_columns([
            pl.col("Ensembl Id").cast(pl.Categorical),
            pl.col("Gene symbol").cast(pl.Categorical)
        ])
        # Use left join to avoid data loss before normalization
        df_pl = df_pl.join(gene_map, on="Ensembl Id", how="left")
        # Ensure every gene has a name, falling back to Ensembl Id if Symbol is missing
        df_pl = df_pl.with_columns(pl.col("Gene symbol").fill_null(pl.col("Ensembl Id")))
        gene_col = "Gene symbol"
    else:
        gene_col = "Ensembl Id"

    # Create a unique identifier for each cell (using established SEPARATOR)
    SEPARATOR = '|||'
    df_pl = df_pl.with_columns(
        (pl.col('Sample').cast(str) + pl.lit(SEPARATOR) + pl.col('Cell Barcode').cast(str))
        .cast(pl.Categorical)
        .alias('UniqueCellId')
    )

    log_message("Creating sparse matrix from long format data", "STEP")
    
    # Extract integer codes directly from categorical columns
    row_codes_raw = df_pl['UniqueCellId'].to_physical().to_numpy()
    col_codes_raw = df_pl[gene_col].to_physical().to_numpy()
    # Use float32 for expression values (Scanpy standard)
    expression_values = df_pl['Raw gene expression'].cast(pl.Float32).to_numpy()

    # Remap codes to 0-indexed contiguous using np.unique
    unique_row_codes_phys, row_codes = np.unique(row_codes_raw, return_inverse=True)
    unique_col_codes_phys, col_codes = np.unique(col_codes_raw, return_inverse=True)
    row_codes = row_codes.astype(np.int32)
    col_codes = col_codes.astype(np.int32)

    # QUALITY FIX: Synchronize labels with the remapped codes
    unique_cell_ids = df_pl['UniqueCellId'].cat.get_categories().gather(unique_row_codes_phys).to_pandas()
    unique_gene_ids = df_pl[gene_col].cat.get_categories().gather(unique_col_codes_phys).to_pandas()

    # Delete Polars objects to free memory
    del df_pl, row_codes_raw, col_codes_raw
    
    # Pre-populate obs with Sample and Cell Barcode vectorially for efficient processing
    obs_df = pd.DataFrame(index=unique_cell_ids)
    split_ids = pd.Series(unique_cell_ids.values).str.split(SEPARATOR, n=1, expand=True, regex=False)
    obs_df['Sample'] = split_ids[0].values
    obs_df['Cell Barcode'] = split_ids[1].values

    # Create the sparse matrix and AnnData object
    adata = sc.AnnData(
        X=csr_matrix((expression_values, (row_codes, col_codes)), shape=(len(unique_cell_ids), len(unique_gene_ids)), dtype=np.float32),
        obs=obs_df,
        var=pd.DataFrame(index=unique_gene_ids)
    )

    log_message(f"AnnData object created: {adata.n_obs} cells × {adata.n_vars} genes", "DONE")
    log_message("Normalizing data (CPM 10k + log1p)", "STEP")
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    return adata

def annotate_cells(adata, model_path, mode="best match", clean_labels=True):
    """
    Annotate cells using CellTypist (v1.6.3) and extract confidence scores.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    log_message(f"Loading model from: {model_path}", "STEP")
    model = models.Model.load(model_path)

    log_message(f"Annotating cells using mode: {mode}", "STEP")
    result = celltypist.annotate(
        adata,
        model,
        majority_voting=(mode == "majority voting")
    )

    # Convert to AnnData to get confidence scores and predicted labels
    log_message("Extracting labels and confidence scores", "STEP")
    annotated = result.to_adata(insert_labels=True, insert_conf=True)

    # Optionally clean the labels
    labels = annotated.obs["predicted_labels"]
    if clean_labels:
        log_message("Cleaning label formatting (removing leading numbers)", "STEP")
        labels = labels.str.replace(r"^\d+\s+", "", regex=True)

    # Add cleaned metadata back to original adata
    adata.obs["Cell type"] = labels.values
    adata.obs["Confidence score"] = annotated.obs["conf_score"].values

    log_message("Annotation complete", "DONE")
    return adata

def save_results(adata, output_csv):
    """
    Save annotated results to CSV.
    """
    log_message(f"Saving results to: {output_csv}", "STEP")
    adata.obs[["Sample", "Cell Barcode", "Cell type", "Confidence score"]].to_csv(output_csv, index=False)
    log_message("Results saved successfully", "DONE")

def main():
    parser = argparse.ArgumentParser(description="Offline CellTypist annotation for scRNA-seq data in long format.")
    parser.add_argument("input_csv", help="Path to raw counts CSV file (long format)")
    parser.add_argument("output_csv", help="Path to save annotated results")
    parser.add_argument("model_path", help="Path to CellTypist .pkl model")
    parser.add_argument("--gene_map", help="Optional gene mapping CSV (Ensembl Id → Gene symbol)", default=None)
    parser.add_argument("--mode", choices=["best match", "majority voting"], default="best match",
                        help="Annotation strategy (default: best match)")
    parser.add_argument("--clean_labels", type=lambda x: x.lower() in ["true", "1", "yes"], default=True,
                        help="Remove leading numbers in cell type labels (default: True)")

    args = parser.parse_args()

    adata = load_data_long_format(args.input_csv, args.gene_map)
    adata = annotate_cells(adata, args.model_path, args.mode, args.clean_labels)
    save_results(adata, args.output_csv)

if __name__ == "__main__":
    main()
