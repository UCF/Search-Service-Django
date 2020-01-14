import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

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

    return this.httpClient.get(apiURL, { params }).pipe(
      // catchError(this.handleError<any[]>('httpService', []))
    );
  }

  private handleError<T>(operation = 'operation', result?: T) {
    return (error: any): Observable<T> => {
      // TODO: Display error message
      console.error(`${operation} failed: ${error.message}`);
      // Let the app keep running by returning an empty result.
      return of(result as T);
    };
  }
}
