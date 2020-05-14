#!/bin/sh

# gettext_copy.sh
# Copy the German and Dutch translation files to the appropriate locale directory

base="aacircuit_de"
cp ./${base}.mo ../application/locale/de/LC_MESSAGES/aacircuit.mo
cp ./${base}.po ../application/locale/de/LC_MESSAGES/aacircuit.po

base="aacircuit_nl"
cp ./${base}.mo ../application/locale/nl/LC_MESSAGES/aacircuit.mo
cp ./${base}.po ../application/locale/nl/LC_MESSAGES/aacircuit.po
