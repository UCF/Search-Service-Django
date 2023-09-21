import { Component, Input } from '@angular/core';
import { Image } from 'src/app/interfaces/images';

@Component({
  selector: 'app-image-item',
  templateUrl: './image-item.component.html',
  styleUrls: ['./image-item.component.scss']
})
export class ImageItemComponent {
  @Input() image!: Image;
}
