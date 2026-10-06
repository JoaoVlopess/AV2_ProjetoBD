import { Component, Input } from '@angular/core';

import { QueryError } from '../../../shared/models/query.models';

@Component({
  selector: 'app-validation-messages',
  standalone: true,
  templateUrl: './validation-messages.component.html',
  styleUrl: './validation-messages.component.css',
})
export class ValidationMessagesComponent {
  @Input() errors: QueryError[] = [];
  @Input() transportError = '';
  @Input() valid: boolean | null = null;
}
