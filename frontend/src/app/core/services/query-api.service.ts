import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  QueryAnalysisResponse,
  QueryRequest,
} from '../../shared/models/query.models';

@Injectable({ providedIn: 'root' })
export class QueryApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/queries';

  analyze(sql: string): Observable<QueryAnalysisResponse> {
    const request: QueryRequest = { sql };
    return this.http.post<QueryAnalysisResponse>(`${this.baseUrl}/parse`, request);
  }
}
