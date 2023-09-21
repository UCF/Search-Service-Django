import { HttpResponse } from '@angular/common/http';
import { Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { Observable } from 'rxjs';
import { EventResult } from 'src/app/interfaces/events';
import { EventsService } from 'src/app/services/events.service';

@Component({
  selector: 'app-event-results',
  templateUrl: './event-results.component.html',
  styleUrls: ['./event-results.component.scss']
})
export class EventResultsComponent implements OnChanges {
  @Input() query!: string;

  events?: EventResult[]
  loading: boolean = false;;

  constructor(
    private eventsService: EventsService
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['query'].firstChange) return;
    this.getEvents();
  }

  getEvents(): void {
    this.loading = true;

    this.eventsService.getEvents(this.query).subscribe((results) => {
      this.loading = false;
      this.events = results.results;
    });
  }

  get hasResults(): boolean {
    return this.events !== undefined && this.events.length > 0;
  }
}
