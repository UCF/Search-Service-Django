import { map, debounceTime, tap, switchAll, filter, distinctUntilChanged } from 'rxjs/operators';
import { fromEvent } from 'rxjs';
import { HttpService } from './../../service/http.service';
import { Component, OnInit, Output, EventEmitter, ElementRef, ViewChild } from '@angular/core';

@Component({
  selector: 'app-search-box',
  templateUrl: './search-box.component.html',
  styleUrls: ['./search-box.component.scss']
})
export class SearchBoxComponent implements OnInit {
  @ViewChild('queryInput', {static: false}) queryInput: ElementRef;

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
          debounceTime(400), //only search after 400 ms
          distinctUntilChanged(),
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
          if(!response) {
            results.emit(null);
          }
          // news
          if(response && response.headers.get('X-WP-Total')) {
            results.emit({
              "results": response.body,
              "count": response.headers.get('X-WP-Total')
            });
          // program or image
          } else {
            if(response) {
              results.emit(response.body);
            }
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

  updateQuery(query: string) {
    let event = new KeyboardEvent('keyup', {'bubbles': true});
    this.queryInput.nativeElement.value = query;
    this.queryInput.nativeElement.dispatchEvent(event);
  }

  toggle(type: string, set: boolean): void {
    if(set) {
      this.setObservable(type);
      let event = new KeyboardEvent('keyup', {'bubbles': true});
      this.queryInput.nativeElement.dispatchEvent(event);
    } else {
      if(type === 'programs') {
        this.programResults.emit(null);
      } else if(type === 'news') {
        this.newsResults.emit(null);
      } else if(type === 'images') {
        this.imageResults.emit(null);
      }
      this.observables[type].unsubscribe();
    }
  }

  ngOnInit(): void {
    this.setObservable('programs');
    this.setObservable('news');
    this.setObservable('images');
  }

}
