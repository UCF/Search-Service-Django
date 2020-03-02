import { EventDetailsService } from '../../service/event-details.service';
import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: '[app-event-details]',
  templateUrl: './event-details.component.html',
  styleUrls: ['./event-details.component.scss']
})
export class EventDetailsComponent implements OnInit {
  @Input() eventResult: any;

  eventDetails: any;

  constructor(
    private eventDetailService: EventDetailsService
  ) {  }

  ngOnInit() {

    this.eventDetailService.getEventDetails(this.eventResult)
      .subscribe(
        (response: any) => { // on success
          this.eventDetails = response;
        },
        (error: any) => { // on error
          console.error(error);
        });
  }

}
