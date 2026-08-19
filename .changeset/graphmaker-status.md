---
'@platforma-open/milaboratories.cell-type-annotation.model': patch
'@platforma-open/milaboratories.cell-type-annotation.ui': patch
'@platforma-open/milaboratories.cell-type-annotation': patch
---

Link the graph page to calculation status: show the "Configure settings and click Run" placeholder
and the running indicator.

The block was pinned to graph-maker 1.1.199, where `pFrame` is a bare `PFrameHandle | undefined`
and `GraphStatus` has no `noPframe` state — the "Configure ..." placeholder simply did not exist at
that version. It was introduced together with the `OutputWithStatus<PFrameHandle>` prop contract,
so the placeholder and the wrapped output have to move as a pair.

- catalog: `@milaboratories/graph-maker` ^1.1.199 -> ^1.7.2 (resolves 1.7.2, already shipping in
  leiden-clustering). 1.7.x also retires the `./styles` export subpath — CSS now rides along with
  the component import — so the explicit `@milaboratories/graph-maker/styles` import is dropped.
- model: `UMAPPf` and `tSNEPf` move from `output` to `outputWithStatus`, so GraphMaker receives the
  envelope it needs to distinguish "not started" from "running" and to render its own placeholder
  and error states. `plotPcols` and `isRunning` stay plain outputs.
- ui: `defineApp` now wires `progress: () => app.model.outputs.isRunning` and
  `showErrorsNotification: true`. The `isRunning` output already existed but nothing consumed it,
  so the block-level running indicator never lit up.

Also fixes a spurious "Running" flash on dataset selection. The three outputs that feed the graph
page read `ctx.resultPool.getData()` *before* guarding on this block's own `labels` output.
`getData()` subscribes to every data resource in the pool up-front (the SDK deprecates it for
exactly this reason), so any still-resolving upstream made the read unstable, the wrapped output
reported `stable: false`, and GraphMaker rendered a running state — for a block that had never been
run. Hoisting the own-output guard above the pool read, as `dimensionality-reduction` already does,
means the pool is never touched until this block actually has a result.
