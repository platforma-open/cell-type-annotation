import { model } from '@platforma-open/milaboratories.cell-type-annotation.model';
import { defineApp } from '@platforma-sdk/ui-vue';
import MainPage from './pages/MainPage.vue';
import tSNEPage from './pages/tSNE.vue';

export const sdkPlugin = defineApp(model, () => {
  return {
    routes: {
      '/': () => MainPage,
      '/tsne': () => tSNEPage,
    },
  };
});

export const useApp = sdkPlugin.useApp;
