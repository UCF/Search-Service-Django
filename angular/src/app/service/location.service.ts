import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable({
  providedIn: 'root'
})
export class LocationService {

  locationUrl = "https://map.ucf.edu/search/.json";

  constructor(
    private httpClient: HttpClient
  ) { }

  searchLocations(query: string): Observable<any> {
    if (!query.trim()) {
      return of(null);
    }

    const params = new HttpParams()
      .set('q', query)
      .set('extended', 'true');

    return this.httpClient.get(this.locationUrl, { params }).pipe(
      catchError(this.handleError<any[]>('searchLocations', []))
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
