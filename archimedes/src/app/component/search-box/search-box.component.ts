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
  @Output() programLoading: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() programError: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() programResults: EventEmitter<any[]> = new EventEmitter<any[]>();

  @Output() newsLoading: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() newsError: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() newsResults: EventEmitter<any[]> = new EventEmitter<any[]>();

  // TODO: Make this configurable
  programApiUrl = 'https://searchdev.cm.ucf.edu/api/v1/programs/search/';
  newsApiUrl = 'https://wwwqa.cc.ucf.edu/news/wp-json/wp/v2/posts/';

  constructor(
    private httpService: HttpService,
    private elementRef: ElementRef
  ) {}

  setObservable(apiURL: string, loading, errorEmit, results) {
    // convert the `keyup` event into an observable stream
    fromEvent(this.elementRef.nativeElement, 'keyup')
      .pipe (
          map((e:any) => e.target.value), // extract the value of the input
          filter((text:string) => text.length > 2), //filter out if empty
          debounceTime(250), //only search after 250 ms
          tap(() => loading.emit(true)), // Enable loading
          map((query:string) => this.httpService.search(apiURL, query)),
          // discard old events if new input comes in
          switchAll()
          // act on the return of the search
      ).subscribe(
        (data: any[]) => { // on success
          loading.emit(false);
          errorEmit.emit(false);
          results.emit(data);
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
    this.setObservable(this.programApiUrl, this.programLoading, this.programError, this.programResults);
    this.setObservable(this.newsApiUrl, this.newsLoading, this.newsError, this.newsResults);
  }

}
