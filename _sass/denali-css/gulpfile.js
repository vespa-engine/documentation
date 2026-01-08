"use strict";

const gulp = require("gulp");
const connect = require("gulp-connect-php");
const browserSync = require("browser-sync").create();
const sass = require("gulp-sass");
// const rename = require("gulp-rename");

const siteSass = () => {
  return gulp
    .src("scss/*.scss")
    .pipe(sass.sync({
      outputStyle: 'compressed'
    }).on('error', sass.logError))
    // .pipe(rename({
    //   suffix: '.min'
    // }))
    .pipe(gulp.dest("css"))
    .pipe(browserSync.stream())
};

const disconnect = () => {
  connect.closeServer();
};

gulp.task(
  "serve",
  gulp.series(siteSass, () => {
    connect.server(
      {
        base: ".",
        port: 4000
      },
      () => {
        browserSync.init({
          injectChanges: true,
          proxy: "127.0.0.1:4000"
        });
      }
    );

    gulp.watch("scss/**/*.scss", siteSass).on("change", browserSync.reload);
    gulp.watch("docs/**/*.html").on("change", browserSync.reload);
  })
);

gulp.task("default", gulp.series("serve", disconnect));
