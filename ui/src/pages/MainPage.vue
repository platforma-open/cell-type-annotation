<script setup lang="ts">
import '@milaboratories/graph-maker/styles';
import { PlBlockPage, PlDropdownRef, PlBtnGroup, PlCheckbox, PlRow, PlDropdown } from '@platforma-sdk/ui-vue';
import { useApp } from '../app';
import type { PlRef } from '@platforma-sdk/model';
import { plRefsEqual } from '@platforma-sdk/model';

const app = useApp();

function setInput(inputRef?: PlRef) {
  app.model.args.countsRef = inputRef;
  if (inputRef)
    app.model.args.title = app.model.outputs.countsOptions?.find((o) => plRefsEqual(o.ref, inputRef))?.label;
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

</script>

<template>
  <PlBlockPage>
    <template #title>Settings</template>
    <PlDropdownRef
      v-model="app.model.args.countsRef" :options="app.model.outputs.countsOptions"
      :style="{ width: '320px' }"
      label="Select dataset"
      clearable @update:model-value="setInput"
    />
    <PlDropdown v-model="app.model.args.model" :style="{ width: '320px' }" :options="modelOptions" label="Select model" />
    <PlBtnGroup
      v-model="app.model.args.mode"
      :style="{ width: '320px' }"
      label="Annotation mode"
      :options="shortOptions"
    />
    <PlRow>
      <PlCheckbox v-model="app.model.args.cleanLabels">Clean labels</PlCheckbox>
    </PlRow>
  </PlBlockPage>
</template>
