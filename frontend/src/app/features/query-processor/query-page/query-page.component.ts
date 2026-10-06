import { Component, inject } from '@angular/core';
import { finalize } from 'rxjs';

import { QueryApiService } from '../../../core/services/query-api.service';
import { QueryAnalysisResponse } from '../../../shared/models/query.models';
import { GraphViewerComponent } from '../graph-viewer/graph-viewer.component';
import { ParseResultComponent } from '../parse-result/parse-result.component';
import { QueryEditorComponent } from '../query-editor/query-editor.component';
import { ValidationMessagesComponent } from '../validation-messages/validation-messages.component';

@Component({
  selector: 'app-query-page',
  standalone: true,
  imports: [
    QueryEditorComponent,
    ParseResultComponent,
    ValidationMessagesComponent,
    GraphViewerComponent,
  ],
  templateUrl: './query-page.component.html',
  styleUrl: './query-page.component.css',
})
export class QueryPageComponent {
  private readonly queryApi = inject(QueryApiService);

  loading = false;
  response: QueryAnalysisResponse | null = null;
  transportError = '';

  analyze(sql: string): void {
    this.loading = true;
    this.response = null;
    this.transportError = '';

    this.queryApi
      .analyze(sql)
      .pipe(finalize(() => (this.loading = false)))
      .subscribe({
        next: (response) => (this.response = response),
        error: () => {
          this.transportError =
            'Não foi possível comunicar com o backend. Confirme se o FastAPI está ativo.';
        },
      });
  }

  clear(): void {
    this.response = null;
    this.transportError = '';
  }
}
