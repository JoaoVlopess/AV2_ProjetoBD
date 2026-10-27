import { Component, inject, signal } from '@angular/core';
import { finalize } from 'rxjs';

import { QueryApiService } from '../../../core/services/query-api.service';
import {
  QueryAnalysisResponse,
  TableCardinalities,
} from '../../../shared/models/query.models';
import { CardinalityEditorComponent } from '../cardinality-editor/cardinality-editor.component';
import { GraphViewerComponent } from '../graph-viewer/graph-viewer.component';
import { ParseResultComponent } from '../parse-result/parse-result.component';
import { QueryEditorComponent } from '../query-editor/query-editor.component';
import { ValidationMessagesComponent } from '../validation-messages/validation-messages.component';

@Component({
  selector: 'app-query-page',
  standalone: true,
  imports: [
    QueryEditorComponent,
    CardinalityEditorComponent,
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
  readonly defaultCardinalities = signal<TableCardinalities>({});
  readonly tableCardinalities = signal<TableCardinalities>({});
  readonly cardinalitiesError = signal('');

  constructor() {
    this.queryApi.getCardinalities().subscribe({
      next: (cardinalities) => {
        this.defaultCardinalities.set({ ...cardinalities });
        this.tableCardinalities.set({ ...cardinalities });
      },
      error: () => {
        this.cardinalitiesError.set(
          'Não foi possível carregar as quantidades padrão das tabelas.',
        );
      },
    });
  }

  analyze(sql: string): void {
    this.loading.set(true);
    this.response.set(null);
    this.transportError.set('');

    this.queryApi
      .analyze(sql, this.tableCardinalities())
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

  updateCardinalities(cardinalities: TableCardinalities): void {
    this.tableCardinalities.set(cardinalities);
  }
}
