#!/bin/sh

# Clean python precompiled code
find . -name "*.pyc" -exec rm '{}' ';'

# Clean temporary files
mkdir -p ./tmp
find ./tmp -name "*.aac" -exec rm '{}' ';'
find ./tmp -name "*.txt" -exec rm '{}' ';'
find ./tmp -name "*.pdf" -exec rm '{}' ';'

# Symbol dictionary keys are in English
export LANG=EN
export LC_ALL=EN

# Run the tests
nosetests -s tests/
