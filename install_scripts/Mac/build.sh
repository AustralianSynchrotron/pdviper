#!/bin/bash

VERSION=`python -c 'import version; print version.__version__'`

rm -rf build/ && rm -rf dist/ && python setup_macosx.py py2app
hdiutil create PDViPeR-$VERSION.dmg -srcfolder dist/PDViPeR.app
