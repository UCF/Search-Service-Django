import { ComponentFixture, TestBed } from '@angular/core/testing';

import { EventResultsComponent } from './event-results.component';

describe('EventResultsComponent', () => {
  let component: EventResultsComponent;
  let fixture: ComponentFixture<EventResultsComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({
      declarations: [EventResultsComponent]
    });
    fixture = TestBed.createComponent(EventResultsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
