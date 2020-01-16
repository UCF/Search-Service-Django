import { HttpService } from './../../service/http.service';
import { fromEvent } from 'rxjs';
import { map, tap, switchAll } from 'rxjs/operators';
import { Component, OnInit, Output, EventEmitter, ElementRef, Input } from '@angular/core';

@Component({
  selector: 'app-show-more',
  templateUrl: './show-more.component.html',
  styleUrls: ['./show-more.component.scss']
})
export class ShowMoreComponent implements OnInit {
  @Input() offset: number;
  @Input() query: string;

  @Output() programLoading: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() programError: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() programResults: EventEmitter<any> = new EventEmitter<any>();

  @Output() newsLoading: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() newsError: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() newsResults: EventEmitter<any> = new EventEmitter<any>();

  constructor(
    private elementRef: ElementRef,
    private httpService: HttpService
  ) { }

  setShowMore(
    searchType: string,
    loading: EventEmitter<boolean>,
    errorEmit: EventEmitter<boolean>,
    results: EventEmitter<any>) {

    // convert the `click` event into an observable stream
    fromEvent(this.elementRef.nativeElement, 'click')
      .pipe(
        tap(() => loading.emit(true)), // Enable loading
        map(() => this.httpService.search(searchType, this.query, "5")),
        // discard old events if new input comes in
        switchAll()
        // act on the return of the search
      ).subscribe(
        (response: any) => { // on success
          loading.emit(false);
          errorEmit.emit(false);
          // news
          if (response.headers.get('X-WP-Total')) {
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

  ngOnInit() {
    this.setShowMore('programs', this.programLoading, this.programError, this.programResults);
    this.setShowMore('news', this.newsLoading, this.newsError, this.newsResults);
  }

}
