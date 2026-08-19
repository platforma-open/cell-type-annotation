import pandas as pd
import polars as pl
import scanpy as sc
import celltypist
from celltypist import models
import argparse
import gc
import os
import numpy as np
import time
from scipy.sparse import csr_matrix

np.random.seed(0)

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
    temp_scan = pl.scan_parquet(file_path)
    file_schema = temp_scan.collect_schema()
    column_names = set(file_schema.keys())

    # Pick the repeated string columns worth holding as categoricals. Parquet carries its own
    # dtypes, so the cast rides in the scan plan instead of going through schema_overrides.
    categorical_candidates = ["Sample", "Ensembl Id", "Cell Barcode", "Cell ID", "CellId"]
    categorical_columns = [col for col in categorical_candidates if col in column_names]

    log_message(f"Reading Parquet with categorical types for: {categorical_columns}", "STEP")

    df_pl = temp_scan.with_columns(
        [pl.col(col).cast(pl.Categorical) for col in categorical_columns]
    ).collect()

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

    # Remap codes to 0-indexed contiguous using np.unique (efficient integer-based mapping)
    u_row_phys, row_idx = np.unique(row_codes_raw, return_inverse=True)
    u_col_phys, col_idx = np.unique(col_codes_raw, return_inverse=True)

    # Map labels to sorted ranks and get sorted unique IDs (efficiently processing only unique labels)
    unique_cell_ids, row_map = np.unique(df_pl['UniqueCellId'].cat.get_categories().gather(u_row_phys).to_numpy(), return_inverse=True)
    unique_gene_ids, col_map = np.unique(df_pl[gene_col].cat.get_categories().gather(u_col_phys).to_numpy(), return_inverse=True)

    # Final row and column codes are the mapped indices
    row_codes = row_map[row_idx].astype(np.int32)
    col_codes = col_map[col_idx].astype(np.int32)

    # Delete Polars objects to free memory
    del df_pl, row_codes_raw, col_codes_raw, u_row_phys, u_col_phys, row_idx, col_idx, row_map, col_map
    
    # Pre-populate obs with Sample and Cell Barcode vectorially for efficient processing
    obs_df = pd.DataFrame(index=unique_cell_ids)
    split_ids = pd.Series(unique_cell_ids).str.split(SEPARATOR, n=1, expand=True, regex=False)
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

DEFAULT_CHUNK_SIZE = 50000

def _predict(adata, model, majority_voting):
    """
    Run CellTypist and return (labels, confidence scores) for the given AnnData.

    Reads AnnotationResult directly instead of going through to_adata(): we only need two
    columns, and this keeps the chunked path below free of any per-chunk AnnData bookkeeping.
    Note this preserves the existing behaviour of reporting the per-cell `predicted_labels`
    even when majority voting is on.
    """
    result = celltypist.annotate(adata, model, majority_voting=majority_voting)
    labels = result.predicted_labels["predicted_labels"]
    conf = result.probability_matrix.max(axis=1)
    return labels.to_numpy(), conf.to_numpy()

def annotate_cells(adata, model_path, mode="best match", clean_labels=True,
                   chunk_size=DEFAULT_CHUNK_SIZE):
    """
    Annotate cells using CellTypist (v1.6.3) and extract confidence scores.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    log_message(f"Loading model from: {model_path}", "STEP")
    model = models.Model.load(model_path)

    majority_voting = (mode == "majority voting")

    if majority_voting or chunk_size <= 0 or adata.n_obs <= chunk_size:
        # Majority voting over-clusters the whole dataset through a global neighbour graph, so
        # its cells cannot be split without changing the result. Small inputs skip chunking too.
        log_message(f"Annotating {adata.n_obs} cells using mode: {mode}", "STEP")
        label_values, conf_values = _predict(adata, model, majority_voting)
    else:
        # CellTypist scales the input by subtracting a dense mean vector from the sparse matrix
        # (classifier.py: `(self.indata[:, k_x_idx] - means_) / sds_`), which densifies it to
        # n_cells x n_model_features float64 - ~45 GB at 500k cells for a 5.6k-feature model -
        # and there is no chunking on its prediction path. Feeding it fixed-size cell batches
        # bounds that allocation; "best match" predicts each cell independently, so the labels
        # and confidence scores are identical to annotating in one shot.
        log_message(
            f"Annotating {adata.n_obs} cells using mode: {mode} "
            f"(in chunks of {chunk_size} to bound peak memory)", "STEP")
        label_chunks = []
        conf_chunks = []
        for start in range(0, adata.n_obs, chunk_size):
            end = min(start + chunk_size, adata.n_obs)
            log_message(f"Annotating cells {start}-{end} of {adata.n_obs}")
            chunk = adata[start:end].copy()
            chunk_labels, chunk_conf = _predict(chunk, model, majority_voting=False)
            label_chunks.append(chunk_labels)
            conf_chunks.append(chunk_conf)
            del chunk
            gc.collect()
        label_values = np.concatenate(label_chunks)
        conf_values = np.concatenate(conf_chunks)

    # Optionally clean the labels
    labels = pd.Series(label_values, index=adata.obs_names, dtype="object")
    if clean_labels:
        log_message("Cleaning label formatting (removing leading numbers)", "STEP")
        labels = labels.str.replace(r"^\d+\s+", "", regex=True)

    adata.obs["Cell type"] = labels.values
    adata.obs["Confidence score"] = conf_values

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
    parser.add_argument("input_csv", help="Path to long-format raw counts Parquet file")
    parser.add_argument("output_csv", help="Path to save annotated results")
    parser.add_argument("model_path", help="Path to CellTypist .pkl model")
    parser.add_argument("--gene_map", help="Optional gene mapping CSV (Ensembl Id → Gene symbol)", default=None)
    parser.add_argument("--mode", choices=["best match", "majority voting"], default="best match",
                        help="Annotation strategy (default: best match)")
    parser.add_argument("--clean_labels", type=lambda x: x.lower() in ["true", "1", "yes"], default=True,
                        help="Remove leading numbers in cell type labels (default: True)")
    parser.add_argument("--chunk_size", type=int, default=DEFAULT_CHUNK_SIZE,
                        help=f"Cells per annotation batch; 0 disables batching (default: {DEFAULT_CHUNK_SIZE})")

    args = parser.parse_args()

    adata = load_data_long_format(args.input_csv, args.gene_map)
    adata = annotate_cells(adata, args.model_path, args.mode, args.clean_labels, args.chunk_size)
    save_results(adata, args.output_csv)

if __name__ == "__main__":
    main()
