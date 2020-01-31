import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class HttpService {
  newsApi: string;
  searchServiceApi: string

  constructor(
    private httpClient: HttpClient
  ) {
    let params = new HttpParams().set('format', 'json');
    this.httpClient.get('/settings/', { params })
    .subscribe(
      (response: any) => { // on success
        this.newsApi = response.ucf_news_api;
        this.searchServiceApi = response.ucf_search_service_api;
      },
      (error: any) => { // on error
        console.error(error);
      });
  }

  search(searchType: string, query: string, offset: string): Observable<any> {

    if (!query || !query.trim() || query.length < 3) {
      return of(null);
    }

    let params;
    // TODO: Make apiUrls configurable
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
