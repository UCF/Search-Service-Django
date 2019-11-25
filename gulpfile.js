const fs    = require('fs');
const gulp  = require('gulp');
const merge = require('merge');

/* eslint-disable no-sync */
if (fs.existsSync('./gulp-config.json')) {
  const overrides = JSON.parse(fs.readFileSync('./gulp-config.json'));
  config = merge(config, overrides);
}
/* eslint-enable no-sync */

gulp.task('default', '');
