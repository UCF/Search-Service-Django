import { Observable } from 'rxjs';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class EventDetailsService {

  constructor(
    private httpClient: HttpClient) { }

  getEventDetails( eventResult: any ): Observable<any> {
    return this.httpClient.get(eventResult.details);
  }
}
