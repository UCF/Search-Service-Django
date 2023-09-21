import { Component, Input, OnInit } from '@angular/core';
import { EventDetail } from 'src/app/interfaces/events';
import { EventsService } from 'src/app/services/events.service';

@Component({
  selector: 'app-event-item',
  templateUrl: './event-item.component.html',
  styleUrls: ['./event-item.component.scss']
})
export class EventItemComponent implements OnInit {
  @Input() eventDetailURL!: string;

  eventDetails!: EventDetail;

  constructor(
    private eventsService: EventsService
  ) {}

  ngOnInit(): void {
    this.eventsService.getEventDetails(this.eventDetailURL).subscribe((result: EventDetail) => {
      this.eventDetails = result;
    });
  }
}
