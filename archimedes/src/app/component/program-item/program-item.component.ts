import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-program-item',
  templateUrl: './program-item.component.html',
  styleUrls: ['./program-item.component.scss']
})
export class ProgramItemComponent implements OnInit {
  @Input() program: any;

  constructor() { }

  ngOnInit() {
  }

}
