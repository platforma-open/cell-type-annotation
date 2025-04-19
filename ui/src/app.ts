import { model } from '@platforma-open/milaboratories.cell-type-annotation.model';
import { defineApp } from '@platforma-sdk/ui-vue';
import MainPage from './pages/MainPage.vue';
import UMAPPage from './pages/UMAP.vue';
import tSNEPage from './pages/tSNE.vue';

export const sdkPlugin = defineApp(model, () => {
  return {
    routes: {
      '/': () => MainPage,
      '/umap': () => UMAPPage,
      '/tsne': () => tSNEPage,
    },
  };
});

export const useApp = sdkPlugin.useApp;
