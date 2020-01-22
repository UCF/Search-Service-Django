import { HttpService } from './../../service/http.service';
import { Component, OnInit, Output, EventEmitter, Input } from '@angular/core';

@Component({
  selector: 'app-show-more',
  templateUrl: './show-more.component.html',
  styleUrls: ['./show-more.component.scss']
})
export class ShowMoreComponent implements OnInit {
  offset = 0;

  @Input() query: string;
  @Input() count: number;
  @Input() searchType: string;
  @Input() limit: number;

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
    private httpService: HttpService
  ) {}

  ngOnInit() {}

  showMore(offset) {
    this.offset = this.offset + offset;
    if(this.searchType === 'programs') {
      this.programLoading.emit(true);
      this.showMoreResults(this.searchType, this.programLoading, this.programError, this.programResults);
    }
    if(this.searchType === 'news') {
      this.newsLoading.emit(true);
      this.showMoreResults(this.searchType, this.newsLoading, this.newsError, this.newsResults);
    }
    if(this.searchType === 'images') {
      this.imageLoading.emit(true);
      this.showMoreResults(this.searchType, this.imageLoading, this.imageError, this.imageResults);
    }
  }

  showMoreResults(
    searchType: string,
    loading: EventEmitter<boolean>,
    error: EventEmitter<boolean>,
    results: EventEmitter<any>) {

    // convert the `click` event into an observable stream
    this.httpService.search(searchType, this.query, this.offset.toString())
      .subscribe(
        (response: any) => { // on success
          loading.emit(false);
          error.emit(false);
          // news
          if (response.headers.get('X-WP-Total')) {
            results.emit({
              "results": response.body,
              "count": response.headers.get('X-WP-Total')
            });
            // program or images
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
          error.emit(false);
        }
      );
  }

}
