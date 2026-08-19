---
'@platforma-open/milaboratories.cell-type-annotation.model': patch
'@platforma-open/milaboratories.cell-type-annotation.ui': patch
'@platforma-open/milaboratories.cell-type-annotation.workflow': patch
'@platforma-open/milaboratories.cell-type-annotation.software': patch
'@platforma-open/milaboratories.cell-type-annotation': patch
---

Migrate the block onto the structurer, fix out-of-memory failures on large datasets, and link the
graph page to calculation status.

**Structurer migration and SDK upgrade.** Adopts the canonical tool-managed layout (oxlint/oxfmt,
tsconfig, turbo, CI workflows, managed package.json + catalog) and the slim facade for the root
block package, on block-tools 2.14.3 — model 1.82.0, ui-vue 1.82.1, workflow-tengo 6.8.2,
tengo-builder 4.0.23, package-builder 3.15.0, test 1.82.4. block-tools 2.14.x also requires a
sibling `kind/` package, added here with an intentionally empty init-params contract: everything
this block needs is chosen in the UI after creation, and the V1 model API has no `init()` to
receive params. Author-code fixes for the SDK majors: explicit type argument on the `isPColumn`
filters feeding `createPFrame`, removal of the retired `@platforma-sdk/ui-vue/styles` import, the
model export renamed `model` -> `platforma` for the facade, and removal of two vestigial workflow
devDeps (`software-small-binaries`, `software-pframes-conv`) that no tengo source imports and whose
stale pin clashed with the copy workflow-tengo 6.8.2 now vendors.

**Out-of-memory on large datasets.** A 243M-row input was OOM-killed against a 32 GiB limit. Three
changes, none of which alter results — verified bit-identical against the previous implementation
on the real dataset:

- workflow: the counts matrix is exported as Parquet rather than CSV, with a dedicated 32 GiB / 4
  CPU budget for that conversion. Counts are one row per non-zero (cell, gene) pair with three
  high-cardinality string columns — the worst case for CSV text encoding — and upstream blocks
  already store the column as Parquet, so the export was inflating columnar data into text for no
  benefit. The annotate step moves to the same budget. The gene-map input stays CSV.
- software: the count matrix is built from the categoricals' integer codes instead of their
  strings. The gene-symbol left join against all 243M rows cost 10.1 GiB and was replaced by a
  lookup over the ~78k distinct Ensembl Ids (the annotation table is 1:1 on Ensembl Id, so this is
  equivalent, with null or absent symbols still falling back to the Ensembl Id); cell identity is a
  packed integer pair of the Sample and Cell Barcode codes, so label strings are built only for the
  distinct pairs that occur rather than once per row; and the long-format frame is released before
  the remapping stage.
- software: cells are annotated in batches (`--chunk_size`, default 50,000; 0 disables). CellTypist
  scales its input by subtracting a dense mean vector from the sparse matrix, densifying it to
  `n_cells x n_model_features` float64 — ~21 GB at 500k cells for a 5,596-feature model — and
  offers no chunking on its prediction path. `"best match"` predicts each cell independently, so
  batched results are identical; majority voting still runs whole-dataset, since its over-clustering
  needs a global neighbour graph.

**Failure diagnosis.** Annotation failures previously reported `Exited with code -1` with no output:
the runner tails a single log file, preferring stderr, while the script logged to stdout with
Python's default block buffering. The entrypoint now runs `python -u`, `log_message` writes to
stderr with `flush=True`, and every line carries peak RSS alongside the row count read and
milestones through the loader — so a killed run leaves a memory trajectory and a last-reached step.

**Graph page status.** The graph page showed neither the "Configure settings and click Run"
placeholder nor a running indicator. `@milaboratories/graph-maker` moves ^1.1.199 -> ^1.7.2: at
1.1.199 the `pFrame` prop is a bare `PFrameHandle | undefined` and `GraphStatus` has no `noPframe`
state, so the placeholder did not exist at that version — it landed together with the
`OutputWithStatus<PFrameHandle>` prop contract, so the two must move as a pair. 1.7.x also retires
the `./styles` export subpath, so that import is dropped. `UMAPPf` and `tSNEPf` move from `output`
to `outputWithStatus` so GraphMaker receives the envelope it needs, and `defineApp` now wires
`progress` to the existing `isRunning` output. Those outputs also guard on this block's own result
before reading the result pool: `getData()` subscribes to every data resource up-front, which made
the page flash "Running" on dataset selection before the block had ever been run.
