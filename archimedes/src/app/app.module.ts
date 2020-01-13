import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppComponent } from './app.component';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ProgramComponent } from './component/program/program.component';
import { SearchBoxComponent } from './component/search-box/search-box.component';
import { NewsComponent } from './component/news/news.component';

@NgModule({
  declarations: [
    AppComponent,
    ProgramComponent,
    SearchBoxComponent,
    NewsComponent
  ],
  imports: [
    BrowserModule,
    FormsModule,
    HttpClientModule
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
