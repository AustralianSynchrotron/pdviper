.. _installation_root:

***************
Installation
***************

PDViPeR is written in `Python <http://python.org>`_ (2.7 at the time of writing) and has several module dependencies that require installation. For Windows, Linux and Mac users the easiest way to install these dependencies is to install one of the `Enthought Python Distributions <http://www.enthought.com/products/epd.php>`_. The `EPDFree <http://www.enthought.com/products/epd_free.php>`_ distribution contains all the modules on which PDViPeR depends. A typical user can just download and install EPDFree then download and unpack PDViPeR and run it immediately.

Some users might prefer alternatives to EPDFree. For example Academic or Commercial users may prefer to use one of Enthought's other distributions. Other popular Python distributions include `Python(x,y) <http://code.google.com/p/pythonxy/>`_, `WinPython <http://code.google.com/p/winpython/>`_ and ActiveState's `ActivePython <http://www.activestate.com/activepython/downloads>`_, all of which will require installation of at least some of the following dependencies:

.. _python_package_dependencies:

Python package dependencies
---------------------------------

PDViPeR depends on the following Python modules being installed in the Python environment

* `numpy <http://numpy.scipy.org/>`_
* `scipy <http://scipy.org/>`_
* `matplotlib <http://matplotlib.org/>`_
* `traits <http://code.enthought.com/projects/traits/>`_
* `traitsui <http://code.enthought.com/projects/traits_ui/>`_
* `chaco <http://code.enthought.com/projects/chaco/>`_
* `pyface <http://code.enthought.com/projects/traits_gui/>`_
* `wxPython <http://wxpython.org/>`_

Those wishing to build the documentation from source will also need `Sphinx <http://sphinx.pocoo.org/>`_.
For those familiar with installing Python packages, the dependencies can be found in the `central repository of Python modules <http://pypi.python.org/pypi>`_. For Microsoft Windows users, Christoph Gohlke (C.G.) maintains a useful `repository of Windows installers <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`_ for many modules. Linux users can typically find the dependencies using their package manager (e.g. synaptic or yum). Mac users should visit the individual sites linked above for instructions.

.. _example1:

Example 1. Windows installation using Enthought Python Distribution (recommended)
---------------------------------------------------------------------------------

Note: untested.

#. Visit the `Enthought website <http://www.enthought.com/products/epd.php>`_, choose a distribution, download and install it. Note, `EPDFree <http://www.enthought.com/products/epd_free.php>`_ satisfies the dependencencies listed above.
#. Verify that Python is running correctly.
   e.g. for Windows 7, click on ``Start Menu|All Programs|Accessories|Command Prompt``.
   At the ``>`` prompt type ``python -c "print 'hello world'"`` noting single and double quotes.
   Verify that ``hello world`` is displayed.
#. Visit the `PDViPeR download page <http://www.synchrotron.org.au/pdviper>`_ and follow the instructions to obtain the package.
#. The main application file is ``app.py`` in the directory into which PDViPeR was unpacked. Run PDViPeR by running the ``start_pdviper.bat`` file or ``app.py`` file.
#. You can create a shortcut by right-clicking ``start_pdviper.bat``, choosing `Copy` in the popup menu, then right-clicking and choosing ``Paste shortcut`` in your desired location.

Example 2. Windows installation using Python(x,y) (optional)
------------------------------------------------------------

Note: untested.

#. Visit the `Python(x,y) <http://code.google.com/p/pythonxy/>`_ `downloads page <http://code.google.com/p/pythonxy/wiki/Downloads>`_ and install a distribution.
#. Verify that Python is running correctly (see :ref:`example1`).
#. Visit the `PDViPeR download page <http://www.synchrotron.org.au/pdviper>`_ and follow the instructions to obtain the package.
#. The main application file is ``app.py`` in the directory into which PDViPeR was unpacked. Run PDViPeR by running the ``start_pdviper.bat`` file or ``app.py`` file.

Example 3. Windows installation on a system with Python already installed (experienced)
---------------------------------------------------------------------------------------

Note: untested.

The difficulty with this approach is that Enthought do not provide a simple separate packaged version of their tool suite, which contains traits, traitsui, chaco and pyface, so the idea is to build these from source code. This can be tricky in Windows. Luckily, at the time of writing, there is a separately packaged version available on the `Python(x,y) downloads page <http://code.google.com/p/pythonxy/wiki/Downloads>`_.

#. Check the :ref:`package dependency list<python_package_dependencies>` above.
#. The easiest way here is to use the packages provided by Python(x,y) and/or Christoph Gohlke. Here are some suggested links. Follow each link to install the required dependency, taking care to choose packages for Python 2.7 and to choose the 32 or 64 bit package version that matches your Python version.
   For example, if you have Python 2.7 32 bit installed, install in turn 
   `numpy (C.G.) <http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy>`_ (if in doubt choose the numpy-MKL-... version),
   `scipy (C.G.) <http://www.lfd.uci.edu/~gohlke/pythonlibs/#scipy>`_,
   `matplotlib (C.G.) <http://www.lfd.uci.edu/~gohlke/pythonlibs/#matplotlib>`_,
   `wxPython (C.G.) <http://www.lfd.uci.edu/~gohlke/pythonlibs/#wxpython>`_,
   `ETS (pythonxy) <http://code.google.com/p/pythonxy/wiki/Downloads>`_.

Example 4. Linux installation using Enthought Python Distribution (recommended)
-------------------------------------------------------------------------------

#. Visit the `Enthought website <http://www.enthought.com/products/epd.php>`_, choose a distribution, download and install it according to the instructions. Note, `EPDFree <http://www.enthought.com/products/epd_free.php>`_ satisfies the dependencencies listed above.
#. Verify that Python is running correctly.
   e.g. for Ubuntu, open a terminal.
   At the ``$`` prompt type ``python -c "print 'hello world'"`` noting single and double quotes.
   Verify that ``hello world`` is displayed.
#. Visit the `PDViPeR download page <http://www.synchrotron.org.au/pdviper>`_ and follow the instructions to obtain the package.
#. The main application file is ``app.py`` in the directory into which PDViPeR was unpacked.
#. PDViPeR can be started by running ``./start_pdviper.sh`` or ``./app.py``. To do this,
   at the ``$`` prompt type ``chmod 777 start_pdviper.sh app.py`` followed by, for example, ``./start_pdviper.sh``

Example 5. Linux installation using synaptic (experienced)
----------------------------------------------------------

Note: untested.

This description is for Ubuntu Linux. yum packaged names in Fedora Linux flavours should have similar names.

#. First, verify that Python2.7 is running correctly.
   e.g. for Ubuntu, open a terminal.
   At the ``$`` prompt type ``python -c "import sys; print sys.version"``.
   Verify that a string displays identifying a 2.7 branch version of Python.
#. Using synaptic or ``apt-get install <package>`` install the following packages: ``python-numpy``, ``python-scipy``, ``python-matplotlib``, ``python-traits``, ``python-traitsui``, ``python-chaco``, ``python-pyface``, ``python-wxgtk2.8``
#. Visit the `PDViPeR download page <http://www.synchrotron.org.au/pdviper>`_ and follow the instructions to obtain the package.
#. The main application file is ``app.py`` in the directory into which PDViPeR was unpacked.
#. PDViPeR can be started by running ``./start_pdviper.sh`` or ``./app.py``. To do this,
   at the ``$`` prompt type ``chmod 777 start_pdviper.sh app.py`` followed by, for example, ``./start_pdviper.sh``

Example 6. Mac OSX installation (recommended)
---------------------------------------------
