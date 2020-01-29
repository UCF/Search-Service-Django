import { map, debounceTime, tap, switchAll, filter } from 'rxjs/operators';
import { fromEvent } from 'rxjs';
import { HttpService } from './../../service/http.service';
import { Component, OnInit, Output, EventEmitter, ElementRef } from '@angular/core';

@Component({
  selector: 'app-search-box',
  templateUrl: './search-box.component.html',
  styleUrls: ['./search-box.component.scss']
})
export class SearchBoxComponent implements OnInit {
  observables = {
    programs: null,
    news: null,
    images: null
  }

  @Output() query: EventEmitter<string> = new EventEmitter<string>();

  @Output() programLoading: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() programError: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() programResults: EventEmitter<any> = new EventEmitter<any>();

  @Output() newsLoading: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() newsError: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() newsResults: EventEmitter<any> = new EventEmitter<any>();

  @Output() imageLoading: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() imageError: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() imageResults: EventEmitter<any> = new EventEmitter<any>();

  constructor(
    private httpService: HttpService,
    private elementRef: ElementRef
  ) {}

  setObservable(searchType: string) {

    let loading: EventEmitter<boolean>;
    let error: EventEmitter<boolean>;
    let results: EventEmitter<any>;

    if(searchType === 'programs') {
      loading = this.programLoading;
      error = this.programError;
      results = this.programResults;
    }

    if(searchType === 'news') {
      loading = this.newsLoading;
      error = this.newsError;
      results = this.newsResults;
    }

    if(searchType === 'images') {
      loading = this.imageLoading;
      error = this.imageError;
      results = this.imageResults;
    }

    // convert the `keyup` event into an observable stream
    const observable = fromEvent(this.elementRef.nativeElement, 'keyup')
      .pipe (
          map((event: any) => event.target.value), // extract the value of the input
          filter((text: string) => text.length > 2), //filter out if empty
          debounceTime(250), //only search after 250 ms
          tap((query: string) => {
            loading.emit(true);
            this.query.emit(query);
          }),
          map((query: string) => this.httpService.search(searchType, query, "0")),
          // discard old events if new input comes in
          switchAll()
          // act on the return of the search
      ).subscribe(
        (response: any) => { // on success
          loading.emit(false);
          error.emit(false);
          // news
          if(response.headers.get('X-WP-Total')) {
            results.emit({
              "results": response.body,
              "count": response.headers.get('X-WP-Total')
            });
          // program or image
          } else {
            results.emit(response.body)
          }
        },
        (error: any) => { // on error
          console.error(error);
          loading.emit(false);
          error.emit(true);
        },
        () => { // on completion
          loading.emit(false);
          error.emit(true);
        }
      );

      this.observables[searchType] = observable;

  }

  toggle(type: string, set: boolean): void {
    if(set) {
      this.setObservable(type);
    } else {
      this.observables[type].unsubscribe();
    }
    this.programResults.emit(null);
    this.newsResults.emit(null);
    this.imageResults.emit(null);
  }

  ngOnInit(): void {
    this.setObservable('programs');
    this.setObservable('news');
    this.setObservable('images');
  }

}
