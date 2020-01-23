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

  @Output() loading: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() error: EventEmitter<boolean> = new EventEmitter<boolean>();
  @Output() results: EventEmitter<any> = new EventEmitter<any>();

  constructor(
    private httpService: HttpService
  ) { }

  ngOnInit() { }

  showMoreResults(offset) {
    this.offset = this.offset + offset;
    this.loading.emit(true);

    // convert the `click` event into an observable stream
    this.httpService.search(this.searchType, this.query, this.offset.toString())
      .subscribe(
        (response: any) => { // on success
          this.loading.emit(false);
          this.error.emit(false);
          // news
          if (response.headers.get('X-WP-Total')) {
            this.results.emit({
              "results": response.body,
              "count": response.headers.get('X-WP-Total')
            });
            // program or images
          } else {
            this.results.emit(response.body)
          }
        },
        (error: any) => { // on error
          console.error(error);
          this.loading.emit(false);
          this.error.emit(true);
        },
        () => { // on completion
          this.loading.emit(false);
          this.error.emit(false);
        }
      );
  }

}
