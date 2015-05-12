# This file based on the example by Thomas Lecocq at
# http://www.geophysique.be/2011/08/01/pack-an-enthought-traits-app-inside-a-exe-using-py2exe-ets-4-0-edit/
# retrieved 2013-04-05
from distutils.core import setup
import enable
import matplotlib as mpl
import os
import py2exe
import pyface
import traitsui
import zmq
#os.environ["PATH"] = \
#    os.environ["PATH"] + os.path.pathsep + os.path.split(zmq.__file__)[0]

exec(open('version.py').read())
  
includes = []
includes.append('numpy')
includes.append('numpy.core')

includes.append('scipy')
includes.append('scipy.special._ufuncs_cxx')
includes.append('scipy.sparse.csgraph._validation')

includes.append('logging')

includes.append('traits')
includes.append('traits.etsconfig.api.*')
includes.append('traitsui')
includes.append('traitsui.qt4')
includes.append('traitsui.qt4.*')

includes.append('traitsui.editors')
includes.append('traitsui.editors.*')
includes.append('traitsui.extras')
includes.append('traitsui.extras.*')
includes.append('traitsui.menu')
includes.append('traitsui.menu.*')
 
includes.append('kiva')

includes.append('PySide')
includes.append('PySide.*')
includes.append('PySide.QtGui.*')

includes.append('pyface')
includes.append('pyface.*')
includes.append('pyface.ui.qt4.*')
includes.append('pyface.ui.qt4.init')
includes.append('pyface.ui.qt4.action.*')
includes.append('pyface.ui.qt4.timer.*')
includes.append('pyface.ui.qt4.wizard.*')
includes.append('pyface.ui.qt4.workbench.*')
includes.append('pyface.qt.*')
includes.append('pyface.qt.QtGui.*')
 
includes.append('enable')
includes.append('enable.drawing')
includes.append('enable.tools')
includes.append('enable.qt4')
includes.append('enable.qt4.*')

includes.append('mpl_toolkits.mplot3d')

includes.append('pandas')


excludes=['wx', 
          'traitsui.wx', 
          '_ssl',
          'IPython',
          'pyreadline',
          'doctest',
          'optparse',
          'sqlite3',
          'multiprocessing',
          'tornado',
          'tcl',
          'email',
          'nose']


packages = []
 
 
data_folders = []
data_folders.append( ( os.path.join(enable.__path__[0], 'images'), r'enable\images' ) )
data_folders.append( ( os.path.join(pyface.__path__[0], 'images'), r'pyface\images' ) )
data_folders.append( ( os.path.join(pyface.__path__[0], 'dock/images'), r'pyface\dock\images' ) )
data_folders.append( ( os.path.join(pyface.__path__[0], 'ui/qt4/images'), r'pyface\ui\qt4\images' ) )
data_folders.append( ( os.path.join(traitsui.__path__[0], 'image/library'), r'traitsui\image\library' ) )
data_folders.append( ( r'bin', r'bin' ) )


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
    author_email = 'pdviper@synchrotron.org.au',
    version = __version__,
    description = "PDViPeR",
    name = "PDViPeR",
    options = {"py2exe":
        { "optimize": 0,
          "packages": packages,
          "includes": includes,
          "excludes": excludes,
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




