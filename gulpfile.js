var gulp        = require('gulp'),
    configLocal = require('./gulp-config.json'),
    merge       = require('merge');

var configDefault = {
  sync: false,
  syncTarget: 'http://localhost'
},
config = merge(configDefault, configLocal);

gulp.task('default', []);
