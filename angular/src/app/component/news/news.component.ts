import { AppComponent } from './../../app.component';
import { NewsService } from './../../service/news.service';
import { Component, OnInit } from '@angular/core';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-news',
  templateUrl: './news.component.html',
  styleUrls: ['./news.component.scss']
})
export class NewsComponent implements OnInit {

  data: any;

  constructor(
    private newsService: NewsService,
    private appComponent: AppComponent
  ) { }

  ngOnInit() {
    this.appComponent.queryTerm.pipe(
      // wait 300ms after each keystroke before considering the term
      debounceTime(300),
      // ignore new term if same as previous term
      distinctUntilChanged(),
      // switches to the most recent call
      switchMap((term: string) => this.newsService.search(term)),
    ).subscribe((data: any) => {
      this.data = data;
    });
  }

}
