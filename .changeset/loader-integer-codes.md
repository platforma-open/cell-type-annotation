---
'@platforma-open/milaboratories.cell-type-annotation.software': patch
---

Build the count matrix from categorical codes instead of strings.

A production run on 243,333,183 rows was OOMKilled (exit 137) against a 32 GiB limit. With logging
in place the trajectory is explicit: `collect()` reached 16.23 GiB, the gene-symbol left join added
10.1 GiB more (26.32 GiB), and the process died in the next step — building `UniqueCellId` as
`Sample.cast(str) + "|||" + Cell Barcode.cast(str)`, which re-materialises full strings for every
row before casting back to Categorical.

Both operations now run on the categoricals' integer codes:

- the gene map is resolved once per distinct Ensembl Id (~78k) via a lookup rather than joined
  against all 243M rows. The annotation table is 1:1 on Ensembl Id, so this is equivalent to the
  left join, and a missing or null symbol still falls back to the Ensembl Id.
- cell identity is a packed integer pair of the Sample and Cell Barcode codes; label strings are
  built only for the distinct pairs that actually occur, not once per row.
- the long-format frame is released before the remapping stage instead of being held through it.

Verified bit-identical to the previous implementation — obs_names, var_names, obs columns and the
sparse matrix itself — with and without a gene map, over a fixture covering the `Cell ID` rename,
null symbols, Ensembl Ids absent from the map, and many-to-one symbol collapse (where csr must sum
the duplicates).
