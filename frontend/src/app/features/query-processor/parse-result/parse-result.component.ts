import { JsonPipe } from '@angular/common';
import { Component, Input } from '@angular/core';

import { QueryAnalysisResponse } from '../../../shared/models/query.models';

@Component({
  selector: 'app-parse-result',
  standalone: true,
  imports: [JsonPipe],
  templateUrl: './parse-result.component.html',
  styleUrl: './parse-result.component.css',
})
export class ParseResultComponent {
  @Input() response: QueryAnalysisResponse | null = null;
}
