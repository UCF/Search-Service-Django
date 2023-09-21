import { Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { NewsItem } from 'src/app/interfaces/news';
import { NewsService } from 'src/app/services/news.service';

@Component({
  selector: 'app-news-results',
  templateUrl: './news-results.component.html',
  styleUrls: ['./news-results.component.scss']
})
export class NewsResultsComponent implements OnChanges {
  @Input() query!: string;

  newsItems?: NewsItem[];
  loading: boolean = false;

  constructor(
    private newsService: NewsService
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['query'].firstChange) return;

    this.getNews();
  }

  getNews(): void {
    this.loading = true;
    this.newsService.getNews(this.query).subscribe((results) => {
      this.loading = false;
      this.newsItems = results;
    });
  }

  get hasResults(): boolean {
    return this.newsItems !== undefined && this.newsItems.length > 0;
  }
}
