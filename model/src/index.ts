import type { GraphMakerState } from '@milaboratories/graph-maker';
import type {
  InferOutputsType,
  PColumnIdAndSpec,
  PFrameHandle,
  PlRef } from '@platforma-sdk/model';
import {
  BlockModel,
  isPColumn,
  isPColumnSpec,
} from '@platforma-sdk/model';

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

export const model = BlockModel.create()

  .withArgs<BlockArgs>({
    // cleanLabels: true,
    mode: 'best match',
    model: 'human-healthy-immunepopulations',
  })

  .withUiState<UiState>({
    graphStateUMAP: {
      title: 'UMAP',
      template: 'dots',
      currentTab: 'settings',
    },
    graphStateTSNE: {
      title: 'tSNE',
      template: 'dots',
      currentTab: null,
    },
  })

  .argsValid((ctx) => ctx.args.countsRef !== undefined)

  .output('countsOptions', (ctx) =>
    ctx.resultPool.getOptions((spec) => isPColumnSpec(spec)
      && spec.name === 'pl7.app/rna-seq/countMatrix' && spec.domain?.['pl7.app/rna-seq/normalized'] === 'false'
    , { includeNativeLabel: true, addLabelAsSuffix: true }),
  )

  .output('UMAPPf', (ctx): PFrameHandle | undefined => {
    const pCols
      = ctx.resultPool
        .getData()
        .entries.map((c) => c.obj)
        .filter(isPColumn)
        .filter((col) => {
          return col.spec.name === 'pl7.app/rna-seq/umap1'
            || col.spec.name === 'pl7.app/rna-seq/umap2'
            || col.spec.name === 'pl7.app/rna-seq/umap3';
        });

    // enriching with cell type annotation data
    const upstream
      = ctx.outputs?.resolve('labels')?.getPColumns();

    if (upstream === undefined) {
      return undefined;
    }

    return ctx.createPFrame([...pCols, ...upstream]);
  })

  .output('tSNEPf', (ctx): PFrameHandle | undefined => {
    const pCols
      = ctx.resultPool
        .getData()
        .entries.map((c) => c.obj)
        .filter(isPColumn)
        .filter((col) => {
          return col.spec.name === 'pl7.app/rna-seq/tsne1'
            || col.spec.name === 'pl7.app/rna-seq/tsne2'
            || col.spec.name === 'pl7.app/rna-seq/tsne3';
        });

    // enriching with cell type annotation data
    const upstream
      = ctx.outputs?.resolve('labels')?.getPColumns();

    if (upstream === undefined) {
      return undefined;
    }

    return ctx.createPFrame([...pCols, ...upstream]);
  })

  .output('plotPcols', (ctx) => {
    const pCols
    = ctx.resultPool
      .getData()
      .entries.map((c) => c.obj)
      .filter(isPColumn)
      .filter((col) => {
        return ((col.spec.name.slice(0, -1) === 'pl7.app/rna-seq/tsne'
          || col.spec.name.slice(0, -1) === 'pl7.app/rna-seq/umap'));
      });

    // enriching with cell type annotation data
    const upstream
    = ctx.outputs?.resolve('labels')?.getPColumns();

    if (upstream === undefined) {
      return undefined;
    }

    return [...pCols, ...upstream].map(
      (c) =>
        ({
          columnId: c.id,
          spec: c.spec,
        } satisfies PColumnIdAndSpec),
    );
  })

  .output('isRunning', (ctx) => ctx.outputs?.getIsReadyOrError() === false)

  .sections((_ctx) => ([
    { type: 'link', href: '/', label: 'Main' },
  ]))

  .title((ctx) =>
    ctx.args.title
      ? `Cell Type Annotation - ${ctx.args.title}`
      : 'Cell Type Annotation',
  )

  .done();

export type BlockOutputs = InferOutputsType<typeof model>;
