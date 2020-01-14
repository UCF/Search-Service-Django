import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class HttpService {

  constructor(
    private httpClient: HttpClient
  ) { }

  search(searchType: string, query: string): Observable<any> {
    if (!query.trim()) {
      return of(null);
    }

    let params;
    // TODO: apiUrls this configurable
    let apiUrl;

    switch (searchType) {
      case 'programs':
        apiUrl = 'https://searchdev.cm.ucf.edu/api/v1/programs/search/';
        params = new HttpParams().set('search', query);
        break;
      case 'news':
        apiUrl = 'https://wwwqa.cc.ucf.edu/news/wp-json/wp/v2/posts';
        params = new HttpParams().set('tag_slugs[]', query);
        break;
    }

    return this.httpClient.get(apiUrl, { params });
  }
}
