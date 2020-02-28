import { Observable } from 'rxjs';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class EventDetailService {

  constructor(
    private httpClient: HttpClient) { }

  getEventDetails( event: any ): Observable<any> {

    // TODO: add the correct params to be passed to the event API
    let params = new HttpParams()
      .set('format', 'json')
      .set('id', event.id);

    // TODO: Add the correct API URL
    return this.httpClient.get('/settings/', { params });
  }
}
