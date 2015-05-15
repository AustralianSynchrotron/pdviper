#!/usr/bin/env python

import os, sys, shutil, platform, struct

home = 'http://synchrotron.org.au/pdviper'
print 70*'*'
print 'Checking python packages...',

missing = []
for pkg in [
        'numpy',
        'scipy',
        'matplotlib',
        'chaco',
        'traits',
        'traitsui',
        'enable',
        'PySide',
        'pandas',
        'pyface',
        'kiva'
    ]:
    try:
        exec('import '+pkg)
    except:
        missing.append(pkg)

if missing:
    print """
Sorry, this version of Python cannot be used
for PDViPeR. It is missing the following package(s):
\t""",
    for pkg in missing:
        print " ", pkg,
    print
    print "We suggest installing the EPDfree package at\nhttp://www.enthought.com/products/epd_free.php/"
    sys.exit()

if not os.path.exists('bin'):
    os.mkdir('bin')
    open(os.path.join('bin', '__init__.py'), 'w')

src = None
if sys.platform.startswith('linux'):
    src = 'binlinux64-2.7'
elif sys.platform == 'darwin' and platform.machine() == 'x86_64':
    src = 'binmac64-2.7'
elif sys.platform == 'darwin' and platform.machine() == 'i386':
    src = 'binmac2.7'
elif sys.platform == 'win32':
    if struct.calcsize("P")*8 == 64:
        src = 'binwin64-2.7'
    else:
        src = 'binwin2.7'
elif sys.platform == 'darwin':
    print 'Mac OS X, PowerPC -- you will need to run f2py on fsource files'
else:
    print 'Unidentifed platform -- you may need to run f2py on fsource files'

if src:
    files = os.listdir(src)
    for f in files:
        fullfilename = os.path.join(src, f)
        shutil.copy(fullfilename, 'bin')
    print src
