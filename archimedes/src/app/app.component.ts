import { Component, OnInit } from '@angular/core';
import { ConfigService } from './services/config.service';
import { Router } from '@angular/router';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'archimedes';
  currentQuery!: string;

  constructor(
  ) {}

  queryChange(event: any) {
    this.currentQuery = event.target.value;
  }
}
