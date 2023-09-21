import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { EventAPIResponse, EventDetail } from '../interfaces/events';
import { ConfigService } from './config.service';

@Injectable({
  providedIn: 'root'
})
export class EventsService {

  client: HttpClient;
  eventsApiUrl!: string;

  constructor(
    client: HttpClient,
    config: ConfigService
  ) {
    this.client = client;
    config.appConfig.subscribe((config) => {
      this.eventsApiUrl = config.ucf_events_api;
    });
  }

  getEvents(query: string, offset: number = 0): Observable<EventAPIResponse> {
    const params = new HttpParams()
      .set('format', 'json')
      .set('q', query);

    return this.client.get<EventAPIResponse>(
      `${this.eventsApiUrl}/search/feed.json`,
      {
        params
      });
  }

  getEventDetails(url: string): Observable<EventDetail> {
    const params = new HttpParams()
      .set('format', 'json');

    return this.client.get<EventDetail>(url, { params });
  }
}
