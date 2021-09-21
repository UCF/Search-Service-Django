const fs    = require('fs');
const gulp  = require('gulp');
const merge = require('merge');


let config = {
  sync: false,
  syncTarget: 'http://127.0.0.1:8000'
};

/* eslint-disable no-sync */
if (fs.existsSync('./gulp-config.json')) {
  const overrides = JSON.parse(fs.readFileSync('./gulp-config.json'));
  config = merge(config, overrides);
}
/* eslint-enable no-sync */


//
// Default task
// NOTE: Update with actual tasks once we have some
//
gulp.task('default', (done) => { done(); });
