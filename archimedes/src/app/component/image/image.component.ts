import { Component, OnInit, Input, Output, EventEmitter } from '@angular/core';

@Component({
  selector: '[app-image]',
  templateUrl: './image.component.html',
  styleUrls: ['./image.component.scss']
})
export class ImageComponent implements OnInit {
  @Input() images: any;

  @Output() queryEmitter: EventEmitter<string> = new EventEmitter<string>();

  selectedImage: number;

  constructor() { }

  ngOnInit() {}

  updateQuery(query: string) {
    this.queryEmitter.emit(query);
  }

}
