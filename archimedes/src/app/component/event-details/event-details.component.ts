import { EventDetailService } from './../../service/event-detail.service';
import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-event-details',
  templateUrl: './event-details.component.html',
  styleUrls: ['./event-details.component.scss']
})
export class EventDetailsComponent implements OnInit {
  @Input() result: any;

  eventDetails: any;

  constructor(
    private eventDetailService: EventDetailService
  ) {  }

  ngOnInit() {

    this.eventDetailService.getEventDetails( event )
      .subscribe(
        (response: any) => { // on success
          this.eventDetails = response;
        },
        (error: any) => { // on error
          console.error(error);
        });
  }

}
