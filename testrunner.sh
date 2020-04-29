#!/bin/sh

# clean python precompiled code
find . -name "*.pyc" -exec rm '{}' ';'

# run the tests
nosetests-3.7 -s tests/
