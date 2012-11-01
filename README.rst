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

Run
---
To run PDViPeR, just call python on app.py from the cloned project directory: ::

    $ python app.py

Version History
---------------
0.2 This version
    Changed 2d surface plot rendering method
    More robust file renaming of processed files
    Data converted to reciprocal-space units are now supported by all plot types
    Improved behaviour of 3d waterfall plot quality setting
0.1 Initial release

Known Issues
------------
- 2d surface plot sometimes literally "loses the plot" when zooming. The symptom of this is that zooming occasionally shows a blank window. Workaround: If this occurs, click back to the Stacked plot then click back to 2d surface.