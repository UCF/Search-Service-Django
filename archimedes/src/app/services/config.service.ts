import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { AppConfig } from '../interfaces/app-config';
import { Observable, map, tap } from 'rxjs';
import { environment } from 'src/environments/environment';
import { Router } from '@angular/router';

@Injectable({
  providedIn: 'root'
})
export class ConfigService {

  public appConfig!: Observable<AppConfig>;

  constructor(
    private client: HttpClient,
  ) { 
    this.loadAppConfig()
  }

  loadAppConfig(): void {
    this.appConfig = this.client.get<AppConfig>(
      `${environment.searchServiceUrl}/settings/`,
      {
        withCredentials: true
      });
  }
}
