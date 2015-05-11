# Building PDViPER.app for MacOSX 
#
# 1. Install (eg via macports) a standalone Python application
#    (version 2.7), all dependencies that satisfy PDViPer as well as
#    py2app and setuptools obiously
#
# 2. Select appripriate pypowder.so (binmac64-2.7) and copy it into bin/
#    $ cp binmac64-2.7/pypowder.so bin/
#
# 3. Ensure PDViPeR works with the standalone Python installation
#    $ python2.7 app.py
#    $ tail ~/.PDViPeR/logfile.log
#
# 4. Clean build and dist directories if they exist
#    $ rm -rf build/* dist/*
#
# 5. Bundle app
#    $ python2.7 setup_macosx.py py2app
#
# 6. Check bundled app
#    $ dist/PDViPeR.app/Contents/MacOS/PDViPeR
#    $ tail ~/.PDViPeR/logfile.log
#
# 7. Create disk image
#    $ hdiutil create PDViPeR-X.Y.dmg -srcfolder dist/PDViPeR.app
#

import os
from setuptools import setup

exec(open('version.py').read())

# includes = ['enthought', 'matplotlib', 'numpy', 'scipy', 'cocoa', 'chaco', 'traits', 'traitsui', 'pandas' ]
includes = []
includes.extend([# The backends are dynamically imported and thus we need to
                 # tell py2app about them.
                 'kiva.*',
                 'enable.*',
                 'enable.qt4.*',
                 'pyface.*',
                 'pyface.ui.qt4.*',
                 'pyface.ui.qt4.action.*',
                 'pyface.ui.qt4.timer.*',
                 'pyface.ui.qt4.wizard.*',
                 'pyface.ui.qt4.workbench.*',
                 'traitsui.qt4.*',
                 'traitsui.qt4.extra.*'
                 'mpl_toolkits.mplot3d',
                 ])

excludes = []
excludes.extend(['bottleneck', 
                 'cairo', 
                 'Carbon', 
                 'Finder', 
                 'jinja2', 
                 'nose', 
                 'PyQT4',
                 'pytz'
                 'reportlab', 
                 'test', 
                 'tornado', 
                 'wx'])

packages = []

data_files = []
data_folders = [('bin', 'bin')]

# Parsing folders and building the data_files table
for folder, relative_path in data_folders:
    for file in os.listdir(folder):
        f1 = os.path.join(folder,file)
        if os.path.isfile(f1):          # skip directories
            f2 = relative_path, [f1]
            data_files.append(f2)

setup(
    name = 'PDViPeR',
    app = ['app.py'],
    setup_requires = ['py2app'],
    author = 'Gary Ruben, Kieran Spears, Lenneke Jong',
    author_email = 'pdviper@synchrotron.org.au',
    version = __version__,
    description = 'PDViPeR',
    options = {'py2app' : {
        'iconfile': 'pdviper_icon.icns',
        'optimize': 1, # 2 does not work as it strips the docstrings
        'packages': packages,
        'includes': includes,
        'excludes': excludes,
        'dist_dir': 'dist',
        'xref': False,
        'compressed' : True,
        'argv_emulation': False,
    },},
    data_files=data_files)

