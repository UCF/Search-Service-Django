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
  @Output() query: EventEmitter<string> = new EventEmitter<string>();

  @Output() programLoading: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() programError: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() programResults: EventEmitter<any> = new EventEmitter<any>();

  @Output() newsLoading: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() newsError: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() newsResults: EventEmitter<any> = new EventEmitter<any>();

  constructor(
    private httpService: HttpService,
    private elementRef: ElementRef
  ) {}

  setObservable(
    searchType: string,
    loading: EventEmitter<boolean>,
    errorEmit: EventEmitter<boolean>,
    results: EventEmitter<any>) {

    // convert the `keyup` event into an observable stream
    fromEvent(this.elementRef.nativeElement, 'keyup')
      .pipe (
          map((e:any) => e.target.value), // extract the value of the input
          filter((text:string) => text.length > 2), //filter out if empty
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
          errorEmit.emit(false);
          // news
          if(response.headers.get('X-WP-Total')) {
            results.emit({
              "results": response.body,
              "count": response.headers.get('X-WP-Total')
            });
          // program
          } else {
            results.emit(response.body)
          }
        },
        (error: any) => { // on error
          console.error(error);
          loading.emit(false);
          errorEmit.emit(true);
        },
        () => { // on completion
          loading.emit(false);
          errorEmit.emit(true);
        }
      );
  }

  ngOnInit(): void {
    this.setObservable('programs', this.programLoading, this.programError, this.programResults);
    this.setObservable('news', this.newsLoading, this.newsError, this.newsResults);
  }

}
