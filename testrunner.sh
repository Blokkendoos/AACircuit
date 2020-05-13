#!/bin/sh

# clean python precompiled code
find . -name "*.pyc" -exec rm '{}' ';'

# clean temporary files
find ./tmp -name "*.aac" -exec rm '{}' ';'
find ./tmp -name "*.txt" -exec rm '{}' ';'
find ./tmp -name "*.pdf" -exec rm '{}' ';'

# run the tests
nosetests-3.7 -s tests/
