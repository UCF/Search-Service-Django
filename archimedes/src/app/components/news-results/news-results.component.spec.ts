import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NewsResultsComponent } from './news-results.component';

describe('NewsResultsComponent', () => {
  let component: NewsResultsComponent;
  let fixture: ComponentFixture<NewsResultsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [NewsResultsComponent]
    });
    fixture = TestBed.createComponent(NewsResultsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
