.. _installation_root:

***************
Installation
***************

PDViPeR is written in `Python <http://python.org>`_ (2.7 at the time of writing) and has several module dependencies that require installation. For Windows, Linux and Mac users the easiest way to install these dependencies is to install one of the `Enthought Python Distributions <http://www.enthought.com/products/epd.php>`_. The `EPDFree <http://www.enthought.com/products/epd_free.php>`_ distribution contains all the modules on which PDViPeR depends. A typical user can just download and install EPDFree then download and unpack PDViPeR and run it immediately.

Some users might prefer alternatives to EPDFree. For example Academic or Commercial users may prefer to use one of Enthought's other distributions. Other popular Python distributions include `Python(x,y) <http://code.google.com/p/pythonxy/>`_, `WinPython <http://code.google.com/p/winpython/>`_ and ActiveState's `ActivePython <http://www.activestate.com/activepython/downloads>`_, all of which will require installation of at least some of the following dependencies:

* `numpy <http://numpy.scipy.org/>`_
* `scipy <http://scipy.org/>`_
* `matplotlib <http://matplotlib.org/>`_
* `traits <http://code.enthought.com/projects/traits/>`_
* `traitsui <http://code.enthought.com/projects/traits_ui/>`_
* `chaco <http://code.enthought.com/projects/chaco/>`_
* `pyface <http://code.enthought.com/projects/traits_gui/>`_
* `wxPython <http://wxpython.org/>`_

Those wishing to build the documentation from source will also need `Sphinx <http://sphinx.pocoo.org/>`_.
For those familiar with installing Python packages, the dependencies can be found in the `central repository of Python modules <http://pypi.python.org/pypi>`_. For Microsoft Windows users Christoph Gohlke maintains a useful `repository of Windows installers <http://www.lfd.uci.edu/~gohlke/pythonlibs/>`_ for many modules. Linux users can typically find the dependencies using their package manager (e.g. synaptic or yum). Mac users should visit the individual sites linked above for instructions.
