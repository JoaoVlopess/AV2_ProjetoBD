import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  QueryAnalysisResponse,
  QueryRequest,
  TableCardinalities,
} from '../../shared/models/query.models';

@Injectable({ providedIn: 'root' })
export class QueryApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/queries';

  analyze(
    sql: string,
    tableCardinalities: TableCardinalities,
  ): Observable<QueryAnalysisResponse> {
    const request: QueryRequest = {
      sql,
      table_cardinalities: tableCardinalities,
    };
    return this.http.post<QueryAnalysisResponse>(`${this.baseUrl}/parse`, request);
  }

  getCardinalities(): Observable<TableCardinalities> {
    return this.http.get<TableCardinalities>(`${this.baseUrl}/cardinalities`);
  }
}
