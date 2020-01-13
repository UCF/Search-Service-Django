import { Component } from '@angular/core';
import { Subject } from 'rxjs';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'search';
  queryTerm = new Subject<string>();

  constructor() { }

  search(query: string): void {
    this.queryTerm.next(query);
  }
}
