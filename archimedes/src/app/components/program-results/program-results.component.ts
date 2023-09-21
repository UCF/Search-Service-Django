import { Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { Program } from 'src/app/interfaces/programs';
import { ProgramsService } from 'src/app/services/programs.service';

@Component({
  selector: 'app-program-results',
  templateUrl: './program-results.component.html',
  styleUrls: ['./program-results.component.scss']
})
export class ProgramResultsComponent implements OnChanges {
  @Input() query!: string;

  programItems?: Program[];
  loading: boolean = false;

  constructor(
    private programService: ProgramsService
  ) { }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['query'].firstChange) return;

    this.getPrograms();
  }

  getPrograms(): void {
    this.loading = true;

    this.programService.getPrograms(this.query).subscribe((result) => {
      this.loading = false;
      this.programItems = result.results;
    });
  }

  get hasResults(): boolean {
    return this.programItems !== undefined && this.programItems.length > 0;
  }
}
