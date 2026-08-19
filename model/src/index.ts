import type { GraphMakerState } from "@milaboratories/graph-maker";
import type {
  InferOutputsType,
  PColumnIdAndSpec,
  PFrameHandle,
  PlRef,
  TreeNodeAccessor,
} from "@platforma-sdk/model";
import { BlockModel, isPColumn, isPColumnSpec } from "@platforma-sdk/model";

export type UiState = {
  graphStateUMAP: GraphMakerState;
  graphStateTSNE: GraphMakerState;
};

export type BlockArgs = {
  countsRef?: PlRef;
  mode: string;
  // cleanLabels: boolean;
  title?: string;
  model: string;
};

export const platforma = BlockModel.create()

  .withArgs<BlockArgs>({
    // cleanLabels: true,
    mode: "best match",
    model: "human-healthy-immunepopulations",
  })

  .withUiState<UiState>({
    graphStateUMAP: {
      title: "UMAP",
      template: "dots",
      currentTab: "settings",
    },
    graphStateTSNE: {
      title: "tSNE",
      template: "dots",
      currentTab: null,
    },
  })

  .argsValid((ctx) => ctx.args.countsRef !== undefined)

  .output("countsOptions", (ctx) =>
    ctx.resultPool.getOptions(
      (spec) =>
        isPColumnSpec(spec) &&
        spec.name === "pl7.app/rna-seq/countMatrix" &&
        spec.domain?.["pl7.app/rna-seq/normalized"] === "false",
      // && spec.annotations?.['pl7.app/hideDataFromGraphs'] === 'true'
      { includeNativeLabel: false, addLabelAsSuffix: true },
    ),
  )

  .outputWithStatus("UMAPPf", (ctx): PFrameHandle | undefined => {
    // Guard on this block's own result first. ctx.resultPool.getData() subscribes to every
    // data resource in the pool up-front, and any still-resolving upstream makes that read
    // unstable — which the wrapped output reports as `stable: false` and GraphMaker renders
    // as a running state. Reading it before the guard flashed "Running" on dataset selection
    // even though this block had never been run.
    const labels = ctx.outputs?.resolve("labels")?.getPColumns();
    if (labels === undefined) {
      return undefined;
    }

    // enriching with the embedding coordinates from the result pool
    const pCols = ctx.resultPool
      .getData()
      .entries.map((c) => c.obj)
      .filter(isPColumn<TreeNodeAccessor>)
      .filter((col) => {
        return (
          col.spec.name === "pl7.app/rna-seq/umap1" ||
          col.spec.name === "pl7.app/rna-seq/umap2" ||
          col.spec.name === "pl7.app/rna-seq/umap3"
        );
      });

    return ctx.createPFrame([...pCols, ...labels]);
  })

  .outputWithStatus("tSNEPf", (ctx): PFrameHandle | undefined => {
    // Guard on this block's own result first. ctx.resultPool.getData() subscribes to every
    // data resource in the pool up-front, and any still-resolving upstream makes that read
    // unstable — which the wrapped output reports as `stable: false` and GraphMaker renders
    // as a running state. Reading it before the guard flashed "Running" on dataset selection
    // even though this block had never been run.
    const labels = ctx.outputs?.resolve("labels")?.getPColumns();
    if (labels === undefined) {
      return undefined;
    }

    // enriching with the embedding coordinates from the result pool
    const pCols = ctx.resultPool
      .getData()
      .entries.map((c) => c.obj)
      .filter(isPColumn<TreeNodeAccessor>)
      .filter((col) => {
        return (
          col.spec.name === "pl7.app/rna-seq/tsne1" ||
          col.spec.name === "pl7.app/rna-seq/tsne2" ||
          col.spec.name === "pl7.app/rna-seq/tsne3"
        );
      });

    return ctx.createPFrame([...pCols, ...labels]);
  })

  .output("plotPcols", (ctx) => {
    // Guard on this block's own result first. ctx.resultPool.getData() subscribes to every
    // data resource in the pool up-front, and any still-resolving upstream makes that read
    // unstable — which the wrapped output reports as `stable: false` and GraphMaker renders
    // as a running state. Reading it before the guard flashed "Running" on dataset selection
    // even though this block had never been run.
    const labels = ctx.outputs?.resolve("labels")?.getPColumns();
    if (labels === undefined) {
      return undefined;
    }

    // enriching with the embedding coordinates from the result pool
    const pCols = ctx.resultPool
      .getData()
      .entries.map((c) => c.obj)
      .filter(isPColumn<TreeNodeAccessor>)
      .filter((col) => {
        return (
          col.spec.name.slice(0, -1) === "pl7.app/rna-seq/tsne" ||
          col.spec.name.slice(0, -1) === "pl7.app/rna-seq/umap"
        );
      });

    // Return batch corrected UMAP/tSNE if present
    let finalPcols = [];
    const batchCorrected = pCols.filter(
      (col) => col.spec.domain?.["pl7.app/rna-seq/batch-corrected"] === "true",
    );
    if (batchCorrected.length !== 0) {
      finalPcols = pCols.filter(
        (col) => col.spec.domain?.["pl7.app/rna-seq/batch-corrected"] !== "false",
      );
    } else {
      finalPcols = pCols;
    }

    return [...finalPcols, ...labels].map(
      (c) =>
        ({
          columnId: c.id,
          spec: c.spec,
        }) satisfies PColumnIdAndSpec,
    );
  })

  .output("isRunning", (ctx) => ctx.outputs?.getIsReadyOrError() === false)

  .sections((_ctx) => [{ type: "link", href: "/", label: "Main" }])

  .title((ctx) =>
    ctx.args.title ? `Cell Type Annotation - ${ctx.args.title}` : "Cell Type Annotation",
  )

  .done(2);

export type BlockOutputs = InferOutputsType<typeof platforma>;
