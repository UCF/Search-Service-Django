import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';

declare let newsApi: string;
declare let searchServiceApi: string;

@Injectable({
  providedIn: 'root'
})
export class HttpService {

  constructor(
    private httpClient: HttpClient
  ) { }

  search(searchType: string, query: string, offset: string): Observable<any> {

    if (!query || !query.trim()) {
      return of(null);
    }

    let params;
    // TODO: Make apiUrls configurable
    let apiUrl;

    switch (searchType) {
      case 'programs':
        apiUrl = searchServiceApi + '/api/v1/programs/search/';
        params = new HttpParams()
          .set('format', 'json')
          .set('search', query)
          .set('limit', '5')
          .set('offset', offset);
        break;
      case 'news':
        apiUrl = newsApi + '/news/wp-json/wp/v2/posts';
        params = new HttpParams()
          .set('tag_slugs[]', query)
          .set('per_page', '5')
          .set('orderby', 'date')
          .set('offset', offset);
        break;
        case 'images':
          apiUrl = searchServiceApi + '/api/v1/images/search/';
          params = new HttpParams()
            .set('format', 'json')
            .set('search', query)
            .set('limit', '8')
            .set('offset', offset);
          break;
    }

    return this.httpClient.get(apiUrl, { params, observe: 'response' });
  }
}
