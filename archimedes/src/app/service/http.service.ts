import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { BehaviorSubject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class HttpService {
  newsApi: string;
  searchServiceApi: string;

  public eventsApi: BehaviorSubject<string> = new BehaviorSubject<string>('');

  constructor(
    private httpClient: HttpClient
  ) {
    let params = new HttpParams().set('format', 'json');
    this.httpClient.get('/settings/', { params })
      .subscribe(
        (response: any) => { // on success
          this.newsApi = response.ucf_news_api;
          this.eventsApi.next(response.ucf_events_api);
          this.searchServiceApi = response.ucf_search_service_api;
        },
        (error: any) => { // on error
          console.error(error);
        });
  }

  search(searchType: string, query: string, offset: string): Observable<any> {

    if (!query || !query.trim() || query.length < 2) {
      return of(null);
    }

    let params;
    let apiUrl;

    switch (searchType) {
      case 'programs':
        apiUrl = this.searchServiceApi + '/api/v1/programs/search/';
        params = new HttpParams()
          .set('format', 'json')
          .set('search', query)
          .set('limit', '5')
          .set('offset', offset);
        break;
      case 'news':
        apiUrl = this.newsApi + '/news/wp-json/wp/v2/posts';
        params = new HttpParams()
          .set('tag_slugs[]', query)
          .set('per_page', '5')
          .set('orderby', 'date')
          .set('offset', offset);
        break;
      case 'events':
        apiUrl = this.eventsApi.value + '/search/feed.json';
        params = new HttpParams()
          .set('q', query)
        break;
      case 'images':
          apiUrl = this.searchServiceApi + '/api/v1/images/search/';
          params = new HttpParams()
            .set('format', 'json')
            .set('search', query)
            .set('limit', '16')
            .set('offset', offset);
          break;
    }

    return this.httpClient.get(apiUrl, { params, observe: 'response' });
  }
}
