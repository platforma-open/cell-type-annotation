<script setup lang="ts">
import '@milaboratories/graph-maker/styles';
import { PlBlockPage, PlDropdownRef, PlBtnGroup, listToOptions } from '@platforma-sdk/ui-vue';
import { useApp } from '../app';
import type { PlRef } from '@platforma-sdk/model';
import { plRefsEqual } from '@platforma-sdk/model';
import { reactive } from 'vue';

const app = useApp();

function setInput(inputRef?: PlRef) {
  app.model.args.countsRef = inputRef;
  if (inputRef)
    app.model.args.title = app.model.outputs.countsOptions?.find((o) => plRefsEqual(o.ref, inputRef))?.label;
  else
    app.model.args.title = undefined;
}

const data = reactive({
  single: 'Best match',
  // multiple: ['Best match', 'Majority voting'],
  compactBtnGroup: false,
});

const shortOptions = listToOptions(['Best match', 'Majority voting']);

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
      v-model="data.single"
      label="PlBtnGroup"
      :options="shortOptions"
      :compact="data.compactBtnGroup"
    />
  </PlBlockPage>
</template>
