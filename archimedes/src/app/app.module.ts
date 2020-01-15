import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';

import { AppComponent } from './app.component';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ProgramComponent } from './component/program/program.component';
import { SearchBoxComponent } from './component/search-box/search-box.component';
import { NewsComponent } from './component/news/news.component';
import { LoadingIconComponent } from './component/loading-icon/loading-icon.component';
import { SafeHtmlPipe } from './pipe/safe-html.pipe';
import { ProgramItemComponent } from './component/program-item/program-item.component';

@NgModule({
  declarations: [
    AppComponent,
    ProgramComponent,
    SearchBoxComponent,
    NewsComponent,
    LoadingIconComponent,
    SafeHtmlPipe,
    ProgramItemComponent
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
