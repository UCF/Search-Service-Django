import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'UCF-Archimedes-Plugin';
  searchObservableProgram: any;
  selected = {
    program: true,
    news: true,
    image: true
  }

  query: string;

  programResults: any;
  programLoading: boolean;
  programError: boolean;

  newsResults: any;
  newsLoading: boolean;
  newsError: boolean;

  imageResults: any;
  imageLoading: boolean;
  imageError: boolean;

  constructor() { }

  toggleChange(): void {
    console.log('toggle');
  }

  queryUpdated(query: string): void {
    this.query = query;
  }

  updateProgramResults(programs: any): void {
    this.programResults = programs;
  }

  updateNewsResults(news: any): void {
    this.newsResults = news;
  }

  updateImageResults(images: any): void {
    this.imageResults = images;
  }
}
