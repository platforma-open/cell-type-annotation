import pandas as pd
import scanpy as sc
import celltypist
from celltypist import models
import argparse
import os

def load_data_long_format(file_path, gene_map_path=None):
    """
    Load long-format scRNA-seq data and convert to AnnData object.
    Optionally map Ensembl IDs to gene symbols using a mapping file.
    """
    print("🔹 Loading data...")
    df = pd.read_csv(file_path)

    # Normalize minimal expected headers
    df.columns = [c.strip() for c in df.columns]
    if "Cell Barcode" not in df.columns and "Cell ID" in df.columns:
        df = df.rename(columns={"Cell ID": "Cell Barcode"})
    if "Cell Barcode" not in df.columns and "CellId" in df.columns:
        df = df.rename(columns={"CellId": "Cell Barcode"})

    required_cols = {"Sample", "Cell Barcode", "Ensembl Id", "Raw gene expression"}
    if not required_cols.issubset(df.columns):
        missing = list(required_cols - set(df.columns))
        raise ValueError(f"Input file must contain columns: {required_cols}. Missing: {missing}. Found: {list(df.columns)}")

    # Map Ensembl IDs to gene symbols if provided
    if gene_map_path:
        print("🔄 Mapping Ensembl IDs to gene symbols...")
        gene_map = pd.read_csv(gene_map_path)
        gene_map = gene_map[["Ensembl Id", "Gene symbol"]].drop_duplicates()
        df = df.merge(gene_map, on="Ensembl Id", how="inner")
        df["Gene"] = df["Gene symbol"]
    else:
        df["Gene"] = df["Ensembl Id"]

    # Pivot to wide format
    expr = df.pivot_table(
        index="Gene",
        columns=["Sample", "Cell Barcode"],
        values="Raw gene expression",
        fill_value=0
    )
    expr.columns = ['|'.join(col) for col in expr.columns]

    # Create AnnData
    adata = sc.AnnData(expr.T)

    # Add metadata
    obs = pd.DataFrame(
        [x.split('|') for x in adata.obs_names],
        columns=["Sample", "Cell Barcode"],
        index=adata.obs_names
    )
    adata.obs = obs

    print(f"✅ Loaded {adata.n_obs} cells × {adata.n_vars} genes.")
    print("🔹 Normalizing data (CPM 10k + log1p)...")
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    return adata

def annotate_cells(adata, model_path, mode="best match", clean_labels=True):
    """
    Annotate cells using CellTypist (v1.6.3) and extract confidence scores via .to_adata().
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    print(f"🔹 Loading model from: {model_path}")
    model = models.Model.load(model_path)

    print(f"🔹 Annotating cells using mode: {mode}")
    result = celltypist.annotate(
        adata,
        model,
        majority_voting=(mode == "majority voting")
    )

    # Convert to AnnData to get confidence scores
    print("🔄 Converting result to AnnData to extract confidence scores...")
    annotated = result.to_adata(insert_labels=True, insert_conf=True)

    # Optionally clean the labels
    labels = annotated.obs["predicted_labels"]
    if clean_labels:
        print("🧹 Cleaning label formatting (removing leading numbers)...")
        labels = labels.str.replace(r"^\d+\s+", "", regex=True)

    # Add cleaned metadata back to original adata
    adata.obs["Cell type"] = labels
    adata.obs["Confidence score"] = annotated.obs["conf_score"]

    print("✅ Annotation complete.")
    return adata

def save_results(adata, output_csv):
    """
    Save annotated results to CSV.
    """
    print(f"🔹 Saving results to: {output_csv}")
    adata.obs[["Sample", "Cell Barcode", "Cell type", "Confidence score"]].to_csv(output_csv, index=False)
    print("✅ Results saved.")

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
