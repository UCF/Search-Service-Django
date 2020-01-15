import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: '[app-programs]',
  templateUrl: './program.component.html',
  styleUrls: ['./program.component.scss']
})
export class ProgramComponent implements OnInit {
  @Input() programs: any;

  constructor() {}

  ngOnInit() {}

  getUrl(program) {
    if (program.catalog_url) {
      return program.catalog_url;
    } else {
      return program.profiles[0].url;
    }
  }

}
