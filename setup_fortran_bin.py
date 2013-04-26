#!/usr/bin/env python
import os, stat, sys, shutil,platform, subprocess, struct
home = 'http://synchrotron.org.au/pdviper'
print 70*'*'
print 'Checking python packages...',
missing = []
for pkg in ['numpy','scipy','matplotlib','chaco','traits','traitsui']:
    try:
        exec('import '+pkg)
    except:
        missing.append(pkg)

if missing:
    print """Sorry, this version of Python cannot be used
for PDViPeR. It is missing the following package(s):
\t""",
    for pkg in missing: print " ",pkg,
    print
    print "We suggest installing the EPDfree package at\nhttp://www.enthought.com/products/epd_free.php/"
    sys.exit()

if not os.path.exists('bin'):
    os.mkdir('bin')
    open(os.path.join('bin','/__init__.py'),'w')


if sys.platform.startswith('linux'):
    #if platform.processor().find('86') <= -1:
    #    ans = raw_input("Note, GSAS requires an Intel-compatible processor and 32-bit"
    #                    "libraries.\nAre you sure want to continue? [Yes]/no: ")
    #    if ans.lower().fin('no') > -1: sys.exit()    
    src='binlinux64-2.7'
    files = os.listdir('binlinux64-2.7')
    print 'Linux, Intel-compatible'
elif sys.platform == "darwin" and platform.processor() == 'i386':
    src='binmac2.7'
    files= os.listdir('binmac2.7')
    print 'Mac OS X, Intel-compatible'
elif sys.platform == "win32":
    if struct.calcsize("P")*8==64:
        src='binwin64-2.7'
        files=os.listdir('binwin64-2.7')
    else:
        src='binwin2.7'
        files = os.listdir('binwin2.7')   
elif sys.platform == "darwin":
    print 'Mac OS X, PowerPC -- you will need to run f2py on fsource files'
else:
    print 'Unidentifed platform -- you may need to run f2py on fsource files'
if len(files)>0:
    for f in files:
        fullfilename=os.path.join(src,f)
        shutil.copy(fullfilename,'bin')

