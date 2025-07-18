<script setup lang="ts">
import '@milaboratories/graph-maker/styles';
import { PlBlockPage, PlBtnGroup, PlDropdown, PlDropdownRef } from '@platforma-sdk/ui-vue';
import { useApp } from '../app';

import type { PredefinedGraphOption } from '@milaboratories/graph-maker';
import { GraphMaker } from '@milaboratories/graph-maker';
import { plRefsEqual, type PlRef } from '@platforma-sdk/model';
import { ref } from 'vue';

const app = useApp();
const settingsOpen = ref(true);

function setInput(inputRef?: PlRef) {
  app.model.args.countsRef = inputRef;
  if (inputRef)
    app.model.args.title = app.model.outputs.countsOptions?.find((o: { ref: PlRef; label: string }) => plRefsEqual(o.ref, inputRef))?.label;
  else
    app.model.args.title = undefined;
}

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

const defaultOptions: PredefinedGraphOption<'scatterplot-umap'>[] = [
  {
    inputName: 'x',
    selectedSource: {
      kind: 'PColumn',
      name: 'pl7.app/rna-seq/umap1',
      valueType: 'Double',
      axesSpec: [
        {
          name: 'pl7.app/sampleId',
          type: 'String',
        },
        {
          name: 'pl7.app/cellId',
          type: 'String',
        },
      ],
    },
  },
  {
    inputName: 'y',
    selectedSource: {
      kind: 'PColumn',
      name: 'pl7.app/rna-seq/umap2',
      valueType: 'Double',
      axesSpec: [
        {
          name: 'pl7.app/sampleId',
          type: 'String',
        },
        {
          name: 'pl7.app/cellId',
          type: 'String',
        },
      ],
    },
  },
  {
    inputName: 'grouping',
    selectedSource: {
      kind: 'PColumn',
      name: 'pl7.app/rna-seq/cellType',
      valueType: 'String',
      axesSpec: [
        {
          name: 'pl7.app/sampleId',
          type: 'String',
        },
        {
          name: 'pl7.app/cellId',
          type: 'String',
        },
      ],
    },
  },
];

</script>

<template>
  <PlBlockPage>
    <GraphMaker
      v-model="app.model.ui.graphStateUMAP"
      chartType="scatterplot-umap"
      :p-frame="app.model.outputs.UMAPPf"
      :default-options="defaultOptions"
      @run="settingsOpen = false"
    >
      <template v-if="settingsOpen" #settingsSlot>
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
