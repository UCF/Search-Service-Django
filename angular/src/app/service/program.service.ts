import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class ProgramService {

  apiURL = 'https://searchdev.cm.ucf.edu/api/v1/programs/search/';

  constructor(
    private httpClient: HttpClient
  ) { }

  search(query: string): Observable<any> {
    if (!query.trim()) {
      return of(null);
    }
    HttpParams
    const params = new HttpParams()
      .set('search', query);

    return this.httpClient.get(this.apiURL, { params }).pipe(
      catchError(this.handleError<any[]>('searchPrograms', []))
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
