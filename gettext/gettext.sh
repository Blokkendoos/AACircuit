#!/bin/sh

# gettext.sh
# Create a *.pot (for editing in poedit) for all the Python source files

# https://www.cyberciti.biz/faq/bash-get-basename-of-filename-or-directory-name/

# Python strings
for p in ../application/*.py ; do \
f="$(basename -- $p)"; \
echo $f; xgettext -d ${f%%.*} -o ${f%%.*}.pot ${p}; \
done;

# Glade string
for p in ../application/*.glade ; do \
f="$(basename -- $p)"; \
echo $f; xgettext -d ${f%%.*} -o ${f%%.*}.pot ${p}; \
done;

# merge all .pot files
names="names.txt";
rm ${names};
for p in ./*.pot ; do \
f="$(basename -- $p)"; \
echo $f >> ${names}; \
done;

msgcat --use-first -f ${names} -o "aacircuit.pot"

msgcat aacircuit.pot ../application/locale/de/LC_MESSAGES/aacircuit.po -o aacircuit_de.po
msgcat aacircuit.pot ../application/locale/nl/LC_MESSAGES/aacircuit.po -o aacircuit_nl.po
