---
'@platforma-open/milaboratories.cell-type-annotation.model': patch
'@platforma-open/milaboratories.cell-type-annotation.ui': patch
'@platforma-open/milaboratories.cell-type-annotation.workflow': patch
'@platforma-open/milaboratories.cell-type-annotation.software': patch
'@platforma-open/milaboratories.cell-type-annotation': patch
---

Export the counts matrix as Parquet instead of CSV, and give that conversion its own budget.

The `xsv.exportFrame` step that materialises the long-format counts p-column for CellTypist was
OOM-killed on large datasets — the p-frame reaches 240M+ rows and the step ran with a hardcoded
16 GiB / 1 CPU. Counts are one row per non-zero (cell, gene) pair with three high-cardinality
string columns, which is the worst case for CSV text encoding; upstream blocks already store the
column as Parquet, so the export was inflating columnar data into text for no benefit.

- workflow: `xsv.exportFrame([rawCounts], "parquet", ...)` with a dedicated 32 GiB / 4 CPU budget,
  separate from the (much smaller) labels import which keeps 16 GiB / 1 CPU. The intermediate is
  renamed `csvCounts` -> `countsParquet` and `rawCounts.csv` -> `rawCounts.parquet` through
  `cell-type-annotation-calculation`. The annotate step itself also moves to 32 GiB / 4 CPU — it
  builds the full sparse matrix plus an AnnData in memory. The gene-map input stays CSV.
- software: `annotate_cell_types.py` reads the counts via `pl.scan_parquet`, casting the repeated
  string columns to `Categorical` inside the scan plan rather than through
  `read_csv(schema_overrides=...)`.

Migrate the block onto the structurer (block-tools 2.13.0) — full SDK upgrade: model/ui-vue 1.81.1,
workflow-tengo 6.8.2, tengo-builder 4.0.22, package-builder 3.15.0, test 1.81.3. Adopts the
canonical tool-managed layout (oxlint/oxfmt, tsconfig, turbo, CI workflows, managed package.json +
catalog) and the slim facade for the root block package. Author-code fixes for the SDK majors:
explicit type argument on the `isPColumn` filters feeding `createPFrame`, removal of the retired
`@platforma-sdk/ui-vue/styles` import, the model export renamed `model` -> `platforma` for the
facade, and removal of two vestigial workflow devDeps (`software-small-binaries`,
`software-pframes-conv`) that no tengo source imports and whose stale pin clashed with the copy
workflow-tengo 6.8.2 now vendors.
