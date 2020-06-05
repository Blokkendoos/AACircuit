#!/bin/sh

# clean up
rm -rf build dist

# build python executable
pyinstaller-3.7 \
--onefile \
--hidden-import pkg_resources.py2_warn \
--add-data "application/*.glade:." \
--add-data "application/style.css:." \
--add-data "application/aacircuit_logo.bmp:." \
--add-data "application/buttons/*.*:./buttons/" \
--add-data "application/bitmaps/*.bmp:./bitmaps/" \
--add-data "application/components/*.json:./components/" \
--add-data "application/locale/de/LC_MESSAGES/*:./locale/de/LC_MESSAGES" \
--add-data "application/locale/nl/LC_MESSAGES/*:./locale/nl/LC_MESSAGES" \
aacircuit.py

