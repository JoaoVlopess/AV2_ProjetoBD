import { Component, Input } from '@angular/core';

import { GraphData } from '../../../shared/models/query.models';

@Component({
  selector: 'app-graph-viewer',
  standalone: true,
  templateUrl: './graph-viewer.component.html',
  styleUrl: './graph-viewer.component.css',
})
export class GraphViewerComponent {
  @Input() graph: GraphData | null = null;
}
