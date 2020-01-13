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

  search(apiURL: string, query: string): Observable<any> {
    if (!query.trim()) {
      return of(null);
    }
    const params = new HttpParams().set('search', query);

    return this.httpClient.get(apiURL, { params });
  }
}
