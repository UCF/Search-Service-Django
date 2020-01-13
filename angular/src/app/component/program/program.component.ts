import { AppComponent } from './../../app.component';
import { ProgramService } from './../../service/program.service';
import { Component, OnInit } from '@angular/core';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-program',
  templateUrl: './program.component.html',
  styleUrls: ['./program.component.scss']
})
export class ProgramComponent implements OnInit {

  data: any;

  constructor(
    private programService: ProgramService,
    private appComponent: AppComponent
  ) { }

  ngOnInit() {
    this.appComponent.queryTerm.pipe(
      // wait 300ms after each keystroke before considering the term
      debounceTime(300),
      // ignore new term if same as previous term
      distinctUntilChanged(),
      // switches to the most recent call
      switchMap((term: string) => this.programService.search(term)),
    ).subscribe((data: any) => {
      this.data = data;
    });
  }

}
