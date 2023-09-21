import { Component, Input, OnChanges, OnInit, SimpleChanges } from '@angular/core';
import { ImagesService } from 'src/app/services/images.service';

@Component({
  selector: 'app-image-results',
  templateUrl: './image-results.component.html',
  styleUrls: ['./image-results.component.scss']
})
export class ImageResultsComponent implements OnChanges {
  @Input() query!: string;

  imageItems?: any[]
  loading: boolean = false;

  constructor(
    private imageService: ImagesService
  ) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['query'].firstChange) return;

    this.getImages();
  }

  getImages(): void {
    this.loading = true;
    this.imageService.getImages(this.query).subscribe((results) => {
      this.loading = false;
      this.imageItems = results.assets;
    });
  }

  get hasResults(): boolean {
    return this.imageItems !== undefined && this.imageItems.length > 0;
  }
}
