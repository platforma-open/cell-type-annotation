<script setup lang="ts">
import '@milaboratories/graph-maker/styles';
import { PlBlockPage, PlBtnGroup, PlDropdown, PlDropdownRef, PlTabs } from '@platforma-sdk/ui-vue';
import { useApp } from '../app';

import type { PredefinedGraphOption } from '@milaboratories/graph-maker';
import { GraphMaker } from '@milaboratories/graph-maker';
import type { PColumnIdAndSpec, PlRef } from '@platforma-sdk/model';
import { plRefsEqual } from '@platforma-sdk/model';
import { computed, reactive } from 'vue';

const app = useApp();

const data = reactive({
  currentTab: 'umap',
});

const tabOptions = [
  { label: 'UMAP', value: 'umap' },
  { label: 't-SNE', value: 'tsne' },
];

function setInput(inputRef?: PlRef) {
  app.model.args.countsRef = inputRef;
  if (inputRef)
    app.model.args.title = app.model.outputs.countsOptions?.find((o: { ref: PlRef; label: string }) => plRefsEqual(o.ref, inputRef))?.label;
  else
    app.model.args.title = undefined;
}

function getIndex(name: string, pcols: PColumnIdAndSpec[]): number {
  return pcols.findIndex((p) => (p.spec.name === name
  ));
}

/* Function to create default options according to the selected tab */
function createDefaultOptions(
  pcols: PColumnIdAndSpec[] | undefined,
  coord1Name: string,
  coord2Name: string,
): PredefinedGraphOption<'scatterplot-umap'>[] | undefined {
  if (!pcols || pcols.length === 0)
    return undefined;

  const coord1Index = getIndex(coord1Name, pcols);
  const coord2Index = getIndex(coord2Name, pcols);
  const cellTypeIndex = getIndex('pl7.app/rna-seq/cellType', pcols);

  if (coord1Index === -1 || coord2Index === -1)
    return undefined;

  const defaults: PredefinedGraphOption<'scatterplot-umap'>[] = [
    {
      inputName: 'x',
      selectedSource: pcols[coord1Index].spec,
    },
    {
      inputName: 'y',
      selectedSource: pcols[coord2Index].spec,
    },
    {
      inputName: 'grouping',
      selectedSource: pcols[cellTypeIndex].spec,
    },
  ];

  return defaults;
}

const defaultOptions = computed((): PredefinedGraphOption<'scatterplot-umap'>[] | undefined => {
  if (data.currentTab === 'umap') {
    return createDefaultOptions(
      app.model.outputs.plotPcols,
      'pl7.app/rna-seq/umap1',
      'pl7.app/rna-seq/umap2',
    );
  }
  if (data.currentTab === 'tsne') {
    return createDefaultOptions(
      app.model.outputs.plotPcols,
      'pl7.app/rna-seq/tsne1',
      'pl7.app/rna-seq/tsne2',
    );
  }
  return undefined;
});

/* Modify graph state, pframe and default options based on the selected tab */
const graphState = computed({
  get: () => data.currentTab === 'umap' ? app.model.ui.graphStateUMAP : app.model.ui.graphStateTSNE,
  set: (value) => {
    if (data.currentTab === 'umap')
      app.model.ui.graphStateUMAP = value;
    else
      app.model.ui.graphStateTSNE = value;
  },
});

const pFrame = computed(() => data.currentTab === 'umap' ? app.model.outputs.UMAPPf : app.model.outputs.tSNEPf);

/* Use both currentTab and pFrame in :key to force re-render the graph when either args (which changes the pFrame) or the tab changes */

const modelOptions = [
  { text: 'Human healthy immune populations', value: 'human-healthy-immunepopulations' },
  { text: 'Human healthy immune subpopulations', value: 'human-healthy-immunesubpopulations' },
  { text: 'Human healthy skin', value: 'human-healthy-skin' },
  { text: 'Human healthy vascular', value: 'human-healthy-vascular' },
  { text: 'Human healthy prefrontal cortex', value: 'human-healthy-prefrontalcortex' },
  { text: 'Human healthy middle temporal gyrus', value: 'human-healthy-middletemporalgyrus' },
  { text: 'Human healthy hippocampus', value: 'human-healthy-hippocampus' },
  { text: 'Human healthy breast', value: 'human-healthy-breast' },
  { text: 'Human healthy lung', value: 'human-healthy-lung' },
  { text: 'Human healthy heart', value: 'human-healthy-heart' },
  { text: 'Human healthy liver', value: 'human-healthy-liver' },
  { text: 'Human healthy endometrium', value: 'human-healthy-endometrium' },
  { text: 'Human healthy pancreatic islet', value: 'human-healthy-pancreaticislet' },
  { text: 'Human disease colorectal cancer', value: 'human-disease-colorectalcancer' },
  { text: 'Human disease idiopatic pulmonary fibrosis', value: 'human-disease-idiopaticpulmonaryfibrosis' },
  { text: 'Human disease COVID19 blood', value: 'human-disease-covid19-blood' },
  { text: 'Human disease COVID19 lung blood', value: 'human-disease-covid19-lungblood' },
  { text: 'Mouse healthy gut', value: 'mouse-healthy-gut' },
  { text: 'Mouse healthy olfactory bulb', value: 'mouse-healthy-olfactorybulb' },
  { text: 'Mouse healthy liver', value: 'mouse-healthy-liver' },
  { text: 'Mouse healthy brain', value: 'mouse-healthy-brain' },
];

const shortOptions = [
  { text: 'Best match', value: 'best match' },
  { text: 'Majority voting', value: 'majority voting' },
];

</script>

<template>
  <PlBlockPage>
    <GraphMaker
      :key="`${data.currentTab}-${pFrame}`"
      v-model="graphState"
      chartType="scatterplot-umap"
      :p-frame="pFrame"
      :default-options="defaultOptions"
    >
      <template #titleLineSlot>
        <PlTabs v-model="data.currentTab" :options="tabOptions" :style="{ display: 'flex', justifyContent: 'flex-end' }"/>
      </template>
      <template #settingsSlot>
        <PlDropdownRef
          v-model="app.model.args.countsRef"
          :options="app.model.outputs.countsOptions"
          :style="{ width: '320px' }"
          label="Select dataset"
          clearable
          required
          @update:model-value="setInput"
        />
        <PlDropdown
          v-model="app.model.args.model"
          :style="{ width: '320px' }"
          :options="modelOptions"
          label="Select model"
        >
          <template #tooltip>
            <div>
              <strong>CellTypist Model Selection</strong><br/>
              Choose a pre-trained CellTypist model for cell type annotation. The model contains learned gene expression patterns for different cell types.<br/><br/>
              <strong>Model types:</strong><br/>
              • <strong>Human models:</strong> Immune, brain regions, organs, and disease-specific models<br/>
              • <strong>Mouse models:</strong> Brain, gut, liver, and olfactory bulb models<br/>
              • <strong>Disease models:</strong> Cancer, fibrosis, and COVID-19 specific models<br/><br/>
            </div>
          </template>
        </PlDropdown>
        <PlBtnGroup
          v-model="app.model.args.mode"
          :style="{ width: '320px' }"
          label="Annotation mode"
          :options="shortOptions"
        >
          <template #tooltip>
            <div>
              <strong>Annotation Mode</strong><br/>
              Controls the CellTypist annotation strategy for assigning cell types.<br/><br/>
              <strong>Best match:</strong> Assigns the cell type with the highest confidence score. Faster and suitable for most datasets.<br/><br/>
              <strong>Majority voting:</strong> Uses ensemble prediction from multiple models for more robust annotation. Slower but more accurate for complex tissues.<br/><br/>
              <strong>Recommendation:</strong> Use "Best match" for most datasets, "Majority voting" for complex tissues or when accuracy is critical.
            </div>
          </template>
        </PlBtnGroup>
        <!-- <PlRow>
          <PlCheckbox v-model="app.model.args.cleanLabels">Clean labels</PlCheckbox>
        </PlRow> -->
      </template>
    </GraphMaker>
  </PlBlockPage>
</template>
