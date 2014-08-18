# This file based on the example by Thomas Lecocq at
# http://www.geophysique.be/2011/08/01/pack-an-enthought-traits-app-inside-a-exe-using-py2exe-ets-4-0-edit/
# retrieved 2013-04-05
# Quoting the blog entry:
#
# then, to launch the packing, just do:
# $ python setup.py py2exe
#
# The build and packing process takes some time, but it works. The /dist directory contains a lot of
# libraries (~73 MB), there must be a way to cut down the imports, but I have to admit, now that I
# have a successful build, I really don't care if it's 110 MB or 80 MB ! I left the lines to include
# the matplotlib data files, although they are not needed for this example.
#
# To launch the script, just hit "example.exe" in the /dist folder. Note, I set the "console" value
# to "example.py", because I wanted to have a python console running behind my GUI. If you replace
# "console" by "windows", double-clicking "example.exe" will just load your GUI.
#
# Note, tested with Christoph Gohlke's version of py2exe 0.6.10dev

from distutils.core import setup
import py2exe
import os
import glob


import zmq
os.environ["PATH"] = \
    os.environ["PATH"] + os.path.pathsep + os.path.split(zmq.__file__)[0]
  
includes = []
includes.append('numpy')
includes.append('numpy.core')
includes.append('scipy')
includes.append('logging') 
includes.append('wx')
includes.append('wx.*')
 
includes.append('traits')
includes.append('traitsui')

includes.append('traitsui.editors')
includes.append('traitsui.editors.*')
includes.append('traitsui.extras')
includes.append('traitsui.extras.*')
 
includes.append('traitsui.wx')
includes.append('traitsui.wx.*')
 
includes.append('kiva')
 
includes.append('pyface')
includes.append('pyface.*')
includes.append('pyface.wx')
 
includes.append('pyface.ui.wx')
includes.append('pyface.ui.wx.init')
includes.append('pyface.ui.wx.*')
includes.append('pyface.ui.wx.grid.*')
includes.append('pyface.ui.wx.action.*')
includes.append('pyface.ui.wx.timer.*')
includes.append('pyface.ui.wx.wizard.*')
includes.append('pyface.ui.wx.workbench.*')
 
includes.append('enable')
includes.append('enable.drawing')
includes.append('enable.tools')
includes.append('enable.wx')
includes.append('enable.wx.*')

includes.append('mpl_toolkits.mplot3d') 
includes.append('pandas.read_csv')

#includes.append('enable.savage')
#includes.append('enable.savage.*')
#includes.append('enable.savage.svg')
#includes.append('enable.savage.svg.*')
#includes.append('enable.savage.svg.backends')
#includes.append('enable.savage.svg.backends.wx')
#includes.append('enable.savage.svg.backends.wx.*')
#includes.append('enable.savage.svg.css')
#includes.append('enable.savage.compliance')
#includes.append('enable.savage.trait_defs')
#includes.append('enable.savage.trait_defs.*')
#includes.append('enable.savage.trait_defs.ui')
#includes.append('enable.savage.trait_defs.ui.*')
#includes.append('enable.savage.trait_defs.ui.wx')
#includes.append('enable.savage.trait_defs.ui.wx.*')

#includes.append('zmq.utils')
#includes.append('zmq.utils.jsonapi')
#includes.append('zmq.utils.strtypes')
excludes=['_ssl','ipython', 'pyreadline', 'doctest', 'locale','optparse', 'pickle', 'calendar']
packages = []
 
data_folders = []
 
# Traited apps:
ETS_folder = r'C:\Python27\Lib\site-packages'

data_folders.append( ( os.path.join(ETS_folder,r'enable\images'), r'enable\images' ) )
data_folders.append( ( os.path.join(ETS_folder,r'pyface\images'), r'pyface\images' ) )
data_folders.append( ( os.path.join(ETS_folder,r'pyface\dock\images'), r'pyface\dock\images' ) )
data_folders.append( ( os.path.join(ETS_folder,r'pyface\ui\wx\images'), r'pyface\ui\wx\images' ) )
data_folders.append( ( os.path.join(ETS_folder,r'pyface\ui\wx\grid\images'), r'pyface\ui\wx\grid\images' ) )
data_folders.append( ( os.path.join(ETS_folder,r'traitsui\wx\images'), r'traitsui\wx\images' ) )
data_folders.append( ( os.path.join(ETS_folder,r'traitsui\image\library'), r'traitsui\image\library' ) )
data_folders.append( ( os.path.join(ETS_folder,r'enable\savage\trait_defs\ui\wx\data'), r'enable\savage\trait_defs\ui\wx\data' ) )

data_folders.append( ( r'bin', r'bin' ) )

# Matplotlib
import matplotlib as mpl
data_files = mpl.get_py2exe_datafiles()
 
# Parsing folders and building the data_files table
for folder, relative_path in data_folders:
    for file in os.listdir(folder):
        f1 = os.path.join(folder,file)
        if os.path.isfile(f1): # skip directories
            f2 = relative_path, [f1]
            data_files.append(f2)

# data_files.append((r'enable', [os.path.join(ETS_folder, r'enable\images.zip')]))
 
setup(windows = ['app.py'],
    author = "Kieran Spear, Gary Ruben, Lenneke Jong",
    author_email='pdviper@synchrotron.org.au',
    version = "1.2",
    description = "PDViPeR",
    name = "PDViPeR",
    options = {"py2exe": {    "optimize": 0,
                              "packages": packages,
                              "includes": includes,
                              #"excludes": excludes,
                              "dll_excludes": ["MSVCP90.dll", "w9xpopen.exe"],
                              "dist_dir": 'dist',
                              "bundle_files":2,
                              "xref": False,
                              "skip_archive": True,
                              "ascii": False,
                              "custom_boot_script": '',
                              "compressed":False,
                             },},
    data_files=data_files)




