import { Component, Input } from '@angular/core';
import { Program } from 'src/app/interfaces/programs';

@Component({
  selector: 'app-program-item',
  templateUrl: './program-item.component.html',
  styleUrls: ['./program-item.component.scss']
})
export class ProgramItemComponent {
  @Input() program!: Program;
}
