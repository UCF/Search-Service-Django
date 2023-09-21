import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ConfigService } from './config.service';

@Injectable({
  providedIn: 'root'
})
export class ImagesService {

  client: HttpClient;
  mediaGraphApiUrl!: string;
  mediaGraphApiKey!: string;
  mediaGraphOrgId!: string;

  constructor(
    client: HttpClient,
    config: ConfigService
  ) {
    this.client = client;
    config.appConfig.subscribe((config) => {
      this.mediaGraphApiUrl = config.ucf_mediagraph_api_url;
      this.mediaGraphApiKey = config.ucf_mediagraph_api_key;
      this.mediaGraphOrgId = config.ucf_mediagraph_org_id;
    });
  }

  getImages(query: string, offset: number = 0): Observable<any> {
    if (!query) return new Observable();

    const headers = new HttpHeaders()
      .set('Authorization', `Bearer: ${this.mediaGraphApiKey}`)
      .set('OrganizationId', this.mediaGraphOrgId);

    const params = new HttpParams()
      .set('q', query);

    return this.client.get(
      `${this.mediaGraphApiUrl}/assets/search/`,
      {
        params,
        headers
      }
    );
  }
}
