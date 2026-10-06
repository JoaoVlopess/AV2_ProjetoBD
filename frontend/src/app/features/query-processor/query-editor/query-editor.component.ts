import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';

@Component({
  selector: 'app-query-editor',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './query-editor.component.html',
  styleUrl: './query-editor.component.css',
})
export class QueryEditorComponent {
  @Input() loading = false;
  @Output() readonly analyzeQuery = new EventEmitter<string>();
  @Output() readonly clearQuery = new EventEmitter<void>();

  readonly sqlControl = new FormControl(
    'SELECT Nome, Email FROM Cliente;',
    { nonNullable: true, validators: [Validators.required] },
  );

  submit(): void {
    const sql = this.sqlControl.value.trim();
    if (!sql || this.loading) {
      this.sqlControl.markAsTouched();
      return;
    }
    this.analyzeQuery.emit(sql);
  }

  clear(): void {
    this.sqlControl.setValue('');
    this.clearQuery.emit();
  }
}
