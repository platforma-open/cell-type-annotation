<script setup lang="ts">
import '@milaboratories/graph-maker/styles';
import { PlBlockPage, PlDropdownRef, PlBtnGroup, PlCheckbox, PlRow } from '@platforma-sdk/ui-vue';
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
