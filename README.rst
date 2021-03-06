PDViPeR: A data manipulation tool for Powder Diffraction
========================================================

PDViPeR (Powder Diffraction Visualisation, Processing and Reporting)
is a BSD-licensed data manipulation and plotting tool for powder diffraction data.

Features
--------
- Input formats: XYE, XY
- Plotting
    - Raw data
    - Stacked (y-offset) plot
    - 3D waterfall plot
    - TIFF/PNG/JPG raster output
    - PDF/SVG/EPS vector output
- Data processing
    - Merging
    - Scaling
    - Normalisation
    - Regridding
    - Zero/reference angle correction

Future features
---------------
- Metadata collation

Requirements
------------
PDViPeR relies on the (free) `Enthought Python Distribution`_ for easy one-click installation of dependencies.

.. _`Enthought Python Distribution`: http://www.enthought.com/products/epd_free.php

Installation
------------
To install the correct pre-compiled binaries for the peak fitting routines run the install.sh (Linux) or install.bat (Windows)
script after cloning the project. In some case you may get a message about fortran code needing to be compiled by hand.
You will need the f2py tool and a fortran compiler (such as GFortran) installed. Then perfom the following steps:
- cd to the fsource directory
- run 'scons'

Run
---
To run PDViPeR, just call python on app.py from the cloned project directory: ::

    $ python app.py

Version History
---------------
2.0 -Improvements in speed for reading a large number of datasets and 2D surface plots
    -Reading of Bruker V3 RAW format data 
 
1.1 -Improved handling of filename conventions for robustness

1.0 -Automatic curve fitting and manual curve definition for background subtraction
    -Peak detection and fitting 
	-Rescaling and offset of both axes
	-Output of all active datasets into .xyz format
	

0.2 -Changed 2d surface plot rendering method
    -More robust file renaming of processed files
    -Data converted to reciprocal-space units are now supported by all plot types
    -Improved behaviour of 3d waterfall plot quality setting

0.1 -Initial release

Known Issues
------------
- 2d surface plot sometimes literally "loses the plot" when zooming. The symptom of this is that zooming occasionally shows a blank window. Workaround: If this occurs, click back to the Stacked plot then click back to 2d surface.

Acknowledgements
----------------
This product includes software produced by UChicago Argonne, LLC under Contract No. DE-AC02-06CH11357 with the Department of Energy. 
The curve fitting routines included in PDViPeR include fortran source code and python routines adapted from GSAS-II. 
Toby, B. H., & Von Dreele, R. B. (2013). GSAS-II: the genesis of a modern open-source all purpose crystallography software package. Journal of Applied Crystallography, 46(2), 544-549.

