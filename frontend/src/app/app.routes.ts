import { Routes } from '@angular/router';

import { QueryPageComponent } from './features/query-processor/query-page/query-page.component';

export const routes: Routes = [
  {
    path: '',
    component: QueryPageComponent,
    title: 'Processador de Consultas',
  },
  { path: '**', redirectTo: '' },
];
