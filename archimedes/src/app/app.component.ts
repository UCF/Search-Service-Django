import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'UCF-Archimedes-Plugin';
  
  programResults: any;
  programLoading: boolean;
  programError: boolean;

  newsResults: any;
  newsLoading: boolean;
  newsError: boolean;

  constructor() { }

  updateProgramResults(programs: any): void {
    this.programResults = programs;
  }

  updateNewsResults(news: any): void {
    this.newsResults = news;
  }
}
