import { AppComponent } from './../../app.component';
import { LocationService } from './../../service/location.service';
import { Component, OnInit } from '@angular/core';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-location',
  templateUrl: './location.component.html',
  styleUrls: ['./location.component.scss']
})
export class LocationComponent implements OnInit {

  data: any;

  constructor(
    private locationService: LocationService,
    private appComponent: AppComponent
  ) { }

  ngOnInit() {
    this.appComponent.queryTerm.pipe(
      // wait 300ms after each keystroke before considering the term
      debounceTime(300),
      // ignore new term if same as previous term
      distinctUntilChanged(),
      // switches to the most recent call
      switchMap((term: string) => this.locationService.searchLocations(term)),
    ).subscribe((data: any) => {
      this.data = data;
    });
  }





}
