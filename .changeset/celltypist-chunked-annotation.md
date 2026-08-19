---
'@platforma-open/milaboratories.cell-type-annotation.software': patch
---

Annotate cells in batches so large datasets no longer OOM.

CellTypist scales its input by subtracting a dense mean vector from the sparse count matrix
(`classifier.py`: `self.indata = (self.indata[:, k_x_idx] - means_) / sds_`), which densifies it to
`n_cells x n_model_features` float64, then allocates a boolean mask of the same shape on the next
line. For a 5,596-feature model that is ~21 GB of float64 at 500k cells and ~42 GB at 1M, on top of
a roughly 2x transient during the divide — and CellTypist 1.6.3 has no chunking on its prediction
path (only `train.py` batches). This is why the block completed on a small dataset and was
OOM-killed (exit -1) on a larger one.

`annotate_cell_types.py` now feeds CellTypist fixed-size cell batches (`--chunk_size`, default
50,000; 0 disables), which bounds that allocation to the batch. `"best match"` predicts each cell
independently, so results are unchanged — verified bit-identical for both labels and confidence
scores against the block's own Mouse_Whole_Brain model. Majority voting still runs on the whole
dataset, since its over-clustering step needs a global neighbour graph.
