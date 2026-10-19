import { Component, inject, signal } from '@angular/core';
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

  readonly loading = signal(false);
  readonly response = signal<QueryAnalysisResponse | null>(null);
  readonly transportError = signal('');

  analyze(sql: string): void {
    this.loading.set(true);
    this.response.set(null);
    this.transportError.set('');

    this.queryApi
      .analyze(sql)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (response) => this.response.set(response),
        error: () => {
          this.transportError.set(
            'Não foi possível comunicar com o backend. Confirme se o FastAPI está ativo.',
          );
        },
      });
  }

  clear(): void {
    this.response.set(null);
    this.transportError.set('');
  }
}
