import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { NewsItem } from '../interfaces/news';
import { ConfigService } from './config.service';

@Injectable({
  providedIn: 'root'
})
export class NewsService {

  client: HttpClient;
  newsApiUrl!: string;

  constructor(
    client: HttpClient,
    config: ConfigService
  ) {
    this.client = client;
    config.appConfig.subscribe((config) => {
      this.newsApiUrl = config.ucf_news_api;
    });
  }

  getNews(query: string, offset: number = 0): Observable<NewsItem[]> {
    const params = new HttpParams()
      .set('tag_slugs[]', query)
      .set('per_page', 5)
      .set('orderby', 'date')
      .set('offset', offset);

    return this.client.get<NewsItem[]>(
      `${this.newsApiUrl}/posts/`,
      {
        params
      });
  }
}
