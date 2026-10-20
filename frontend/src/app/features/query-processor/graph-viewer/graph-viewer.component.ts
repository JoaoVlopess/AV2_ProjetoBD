import {
  Component,
  ElementRef,
  Input,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
} from '@angular/core';
import cytoscape from 'cytoscape';

import { GraphData } from '../../../shared/models/query.models';

@Component({
  selector: 'app-graph-viewer',
  standalone: true,
  templateUrl: './graph-viewer.component.html',
  styleUrl: './graph-viewer.component.css',
})
export class GraphViewerComponent implements OnChanges, OnDestroy {
  @Input() graph: GraphData | null = null;

  private container?: ElementRef<HTMLDivElement>;
  private cytoscapeGraph?: cytoscape.Core;

  @ViewChild('graphContainer')
  set graphContainer(element: ElementRef<HTMLDivElement> | undefined) {
    this.container = element;

    if (element) {
      this.renderGraph();
    } else {
      this.destroyGraph();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['graph']) {
      this.renderGraph();
    }
  }

  ngOnDestroy(): void {
    this.destroyGraph();
  }

  private renderGraph(): void {
    if (!this.container || !this.graph) {
      return;
    }

    this.destroyGraph();

    const elements = [
      ...this.graph.elements.nodes,
      ...this.graph.elements.edges,
    ] as cytoscape.ElementDefinition[];

    this.cytoscapeGraph = cytoscape({
      container: this.container.nativeElement,
      elements,
      minZoom: 0.35,
      maxZoom: 2,
      wheelSensitivity: 0.2,
      layout: {
        name: 'breadthfirst',
        // Organiza a árvore a partir da projeção, preservando as setas de fluxo.
        directed: false,
        roots: this.graph.elements.nodes
          .filter((node) => node.data['kind'] === 'projection')
          .map((node) => node.data.id),
        direction: 'downward',
        padding: 30,
        spacingFactor: 1.35,
      },
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            shape: 'round-rectangle',
            width: 'label',
            height: 'label',
            padding: '16px',
            'text-wrap': 'wrap',
            'text-max-width': '240px',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '12px',
            color: '#172033',
            'background-color': '#e8eef8',
            'border-color': '#8290a8',
            'border-width': 2,
          },
        },
        {
          selector: 'node[kind = "relation"]',
          style: {
            shape: 'rectangle',
            'background-color': '#e0f2fe',
            'border-color': '#0284c7',
          },
        },
        {
          selector: 'node[kind = "product"]',
          style: {
            'background-color': '#fef3c7',
            'border-color': '#d97706',
          },
        },
        {
          selector: 'node[kind = "selection"]',
          style: {
            'background-color': '#dcfce7',
            'border-color': '#16a34a',
          },
        },
        {
          selector: 'node[kind = "projection"]',
          style: {
            'background-color': '#ede9fe',
            'border-color': '#7c3aed',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2,
            'line-color': '#64748b',
            'target-arrow-color': '#64748b',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
          },
        },
      ],
    });
  }

  private destroyGraph(): void {
    this.cytoscapeGraph?.destroy();
    this.cytoscapeGraph = undefined;
  }
}
