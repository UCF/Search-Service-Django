const fs           = require('fs');
const browserSync  = require('browser-sync').create();
const gulp         = require('gulp');
const autoprefixer = require('gulp-autoprefixer');
const cleanCSS     = require('gulp-clean-css');
const include      = require('gulp-include');
const eslint       = require('gulp-eslint-new');
const isFixed      = require('gulp-eslint-if-fixed');
const babel        = require('gulp-babel');
const rename       = require('gulp-rename');
const sass         = require('gulp-sass')(require('sass'));
const sassLint     = require('gulp-sass-lint');
const sassVars     = require('gulp-sass-vars');
const uglify       = require('gulp-uglify');
const merge        = require('merge');
const del          = require('del');


let config = {
  src: {
    scssPath: './src/scss',
    jsPath: './src/js'
  },
  dist: {
    cssPath: './static/css',
    jsPath: './static/js',
    fontPath: './static/webfonts'
  },
  devPath: './dev',
  packagesPath: './node_modules',
  packageLock: {},
  sync: false,
  syncTarget: 'http://localhost/'
};

/* eslint-disable no-sync */
if (fs.existsSync('./package-lock.json')) {
  config.packageLock = JSON.parse(fs.readFileSync('./package-lock.json'));
}
if (fs.existsSync('./gulp-config.json')) {
  const overrides = JSON.parse(fs.readFileSync('./gulp-config.json'));
  config = merge(config, overrides);
}
/* eslint-enable no-sync */


//
// Helper functions
//

// Base SCSS linting function
function lintSCSS(src) {
  return gulp.src(src)
    .pipe(sassLint())
    .pipe(sassLint.format())
    .pipe(sassLint.failOnError());
}

// Base SCSS compile function
function buildCSS(src, dest, vars) {
  dest = dest || config.dist.cssPath;
  vars = vars || {};

  return gulp.src(src)
    .pipe(sassVars(vars))
    .pipe(sass({
      includePaths: [config.src.scssPath, config.packagesPath]
    })
      .on('error', sass.logError))
    .pipe(cleanCSS())
    .pipe(autoprefixer({
      // Supported browsers added in package.json ("browserslist")
      cascade: false
    }))
    .pipe(rename({
      extname: '.min.css'
    }))
    .pipe(gulp.dest(dest));
}

// Base JS linting function (with eslint). Fixes problems in-place.
function lintJS(src, dest) {
  dest = dest || config.src.jsPath;

  return gulp.src(src)
    .pipe(eslint({
      fix: true
    }))
    .pipe(eslint.format())
    .pipe(isFixed(dest));
}

// Base JS compile function
function buildJS(src, dest) {
  dest = dest || config.dist.jsPath;

  return gulp.src(src)
    .pipe(include({
      includePaths: [config.packagesPath, config.src.jsPath]
    }))
    .on('error', console.log) // eslint-disable-line no-console
    .pipe(babel())
    .pipe(uglify())
    .pipe(rename({
      extname: '.min.js'
    }))
    .pipe(gulp.dest(dest));
}

// BrowserSync reload function
function serverReload(done) {
  if (config.sync) {
    browserSync.reload();
  }
  done();
}

// BrowserSync serve function
function serverServe(done) {
  if (config.sync) {
    browserSync.init({
      proxy: {
        target: config.syncTarget
      }
    });
  }
  done();
}


//
// Installation of components/dependencies
//

// Copy Font Awesome 5 files
gulp.task('move-components-fontawesome-6', (done) => {
  // Delete existing font files
  del(`${config.dist.fontPath}/font-awesome/**/*`);

  // Move font files
  gulp.src(`${config.packagesPath}/@fortawesome/fontawesome-pro/webfonts/**/*`)
    .pipe(gulp.dest(`${config.dist.fontPath}/`));

  done();
});

// Athena Framework web font processing
gulp.task('move-components-athena-fonts', (done) => {
  gulp.src([`${config.packagesPath}/ucf-athena-framework/dist/fonts/**/*`])
    .pipe(gulp.dest(config.dist.fontPath));
  done();
});

// Run all component-related tasks
gulp.task('components', gulp.parallel(
  'move-components-fontawesome-6',
  'move-components-athena-fonts'
));


//
// CSS
//

// Lint all theme scss files
gulp.task('scss-lint-theme', () => {
  return lintSCSS(`${config.src.scssPath}/*.scss`);
});

// Compile theme stylesheet
gulp.task('scss-build-theme', () => {
  return buildCSS(`${config.src.scssPath}/style.scss`);
});

// All theme css-related tasks
gulp.task('css', gulp.series(
  'scss-lint-theme',
  'scss-build-theme'
));


//
// JavaScript
//

// Run eslint on js files in src.jsPath
gulp.task('es-lint-theme', () => {
  return lintJS([`${config.src.jsPath}/*.js`], config.src.jsPath);
});

// Concat and uglify js files through babel
gulp.task('js-build-theme', () => {
  return buildJS(`${config.src.jsPath}/script.js`, config.dist.jsPath);
});

gulp.task('js-build-tagify', () => {
  return buildJS(`${config.src.jsPath}/jobs-tagify.js`, config.dist.jsPath);
});

gulp.task('js-build-highlights', () => {
  return buildJS(`${config.src.jsPath}/highlights-iconpicker.js`, config.dist.jsPath);
});

gulp.task("js-build-quotes", () => {
  return buildJS(`${config.src.jsPath}/quotes.js`, config.dist.jsPath);
});

// All js-related tasks
gulp.task('js', gulp.series('es-lint-theme', 'js-build-theme', 'js-build-tagify', 'js-build-highlights', 'js-build-quotes'));

//
// Rerun tasks when files change
//
gulp.task('watch', (done) => {
  serverServe(done);

  gulp.watch(`${config.src.scssPath}/**/*.scss`, gulp.series('css', serverReload));
  gulp.watch(`${config.src.jsPath}/**/*.js`, gulp.series('js', serverReload));
});


//
// Default task
//
gulp.task('default', gulp.series('components', 'css', 'js'));
