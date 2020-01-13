import { Component, OnInit, Input } from '@angular/core';

@Component({
  selector: 'app-program',
  templateUrl: './program.component.html',
  styleUrls: ['./program.component.scss']
})
export class ProgramComponent implements OnInit {
  @Input() program: any;

  constructor() {}

  ngOnInit() {}

}
