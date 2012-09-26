.. |theta| unicode:: U+03B8   .. theta trimming surrounding whitespace
    :trim:
.. PDViPeR documentation master file, created by
   sphinx-quickstart on Thu Jul 19 17:17:01 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to PDViPeR's documentation!
===================================

`PDViPeR <http://www.synchrotron.org.au/pdviper>`_ [#pdviper_url]_ is a data analysis program developed for use on the Australian Synchrotron (AS) `Powder Diffraction (PD) beamline <http://www.synchrotron.org.au/index.php/aussyncbeamlines/powder-diffraction>`_.
It takes data captured on the Mythen microstrip detector and performs the following post-processing operations:

* Reads .xye and .xy ASCII columnar data files and writes processed files in .xye format
* Visual comparison of datasets.
* Aligns and merges dataset pairs based on a user-specified alignment region.
* Two merge methods (splice and merge) with normalisation to a specified detector position or reference file.
* Outputs plots suitable for publication or editing: Vertically stacked series, interpolated 2D image and 3D waterfall plots.
* X-axis/abscissa rescaling between 2 |theta|, d-space and Q units.

Contents:
=========
.. toctree::
   :maxdepth: 2

   installation
   usage
   about
   parab_file_format

Modules
=======
This section contains auto-generated documentation extracted from the processing module that contains the interpolation, alignment and merging algorithms.

.. toctree::
   :maxdepth: 2

   processing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. [#pdviper_url] `PDViPeR <http://www.synchrotron.org.au/pdviper>`_ -- Powder Diffraction Visualisation Processing and Reporting.

|

----

.. image:: images/synch_logo_60px.png
   :target: http://www.synchrotron.org.au/
   :alt: Australian Synchrotron logo

.. image:: images/nectar_logo_60px.png
   :target: http://nectar.org.au/
   :alt: NeCTAR logo

.. image:: images/versi_logo_60px.png
   :target: http://www.versi.edu.au/
   :alt: VeRSI logo
