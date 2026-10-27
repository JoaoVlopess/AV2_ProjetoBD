import { Component, EventEmitter, Input, Output } from '@angular/core';

import { TableCardinalities } from '../../../shared/models/query.models';

@Component({
  selector: 'app-cardinality-editor',
  standalone: true,
  templateUrl: './cardinality-editor.component.html',
  styleUrl: './cardinality-editor.component.css',
})
export class CardinalityEditorComponent {
  @Input() cardinalities: TableCardinalities = {};
  @Input() defaults: TableCardinalities = {};
  @Input() disabled = false;
  @Input() loadError = '';
  @Output() readonly cardinalitiesChange =
    new EventEmitter<TableCardinalities>();

  tableNames(): string[] {
    return Object.keys(this.cardinalities);
  }

  updateCardinality(table: string, event: Event): void {
    const input = event.target as HTMLInputElement;
    const parsedValue = Number(input.value);
    const cardinality = Number.isFinite(parsedValue)
      ? Math.max(0, Math.trunc(parsedValue))
      : 0;

    input.value = String(cardinality);
    this.cardinalitiesChange.emit({
      ...this.cardinalities,
      [table]: cardinality,
    });
  }

  reset(): void {
    this.cardinalitiesChange.emit({ ...this.defaults });
  }
}
