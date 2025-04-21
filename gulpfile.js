const { src, dest, watch, series } = require('gulp');
const sass = require('gulp-sass')(require('sass'));
const sourcemaps = require('gulp-sourcemaps');

function compileSass() {
    return src('boletines_app/static/boletines_app/scss/**/*.scss')
        .pipe(sourcemaps.init())
        .pipe(sass({outputStyle: 'compressed'}).on('error', sass.logError))
        .pipe(sourcemaps.write('.'))
        .pipe(dest('boletines_app/static/boletines_app/css'));
}

function watchFiles() {
    watch('boletines_app/static/boletines_app/scss/**/*.scss', compileSass);
}

exports.default = series(compileSass, watchFiles);