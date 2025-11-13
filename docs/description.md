# Overview

Automatically annotates cell types in single-cell RNA sequencing data using pre-trained CellTypist models. The block takes normalized gene expression data as input and assigns cell type labels to individual cells based on learned gene expression patterns from reference datasets. CellTypist uses a logistic regression classifier trained on reference cell populations to predict cell types, providing both cell type assignments and confidence scores for each cell.

The block supports multiple pre-trained models covering various tissues and conditions (e.g., immune populations, brain regions, organ-specific cell types) for both human and mouse species. Annotation can be performed in different modes to balance accuracy and specificity. The resulting cell type annotations can be used for downstream analyses such as compositional analysis, differential expression analysis, and visualization of cell type distributions across experimental conditions.

The block uses CellTypist for cell type annotation. When using this block in your research, cite the CellTypist publication (Domínguez Conde et al. 2022) listed below.

The following publication describes the methodology used:

> Domínguez Conde, C., Xu, C., Jarvis, L. B. et al. (2022). Cross-tissue immune cell analysis reveals tissue-specific features in humans. _Science_ **376**, eabl5197 (2022). [https://doi.org/10.1126/science.abl5197](https://doi.org/10.1126/science.abl5197)