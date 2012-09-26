.. |degree| unicode:: U+00B0   .. degree trimming surrounding whitespace
    :ltrim:

.. _usage_root:

Usage
*****

PDViPeR is laid out so that .xye files can be quickly loaded and viewed without delving into the processing options. The processing options are organised within tabs of the panel adjacent to the main plot window.

Assumptions about the data
==========================
* `Format of .xy and .xye files <http://www.synchrotron.org.au/index.php/aussyncbeamlines/powder-diffraction/data-analysis/data-formats>`_
* `Format of .parab files <http://www.synchrotron.org.au/index.php/aussyncbeamlines/powder-diffraction/data-analysis/data-formats>`_
* One .parab file per _p1_-_p4_ file

Reading data
============

Processing
==========

Merging datasets
----------------
The Mythen detector array on the AS PD beamline consists of several adjacent strip detectors separated by small gaps, and covering a total angular range of approximately 80 |degree|. Consequently, the acquired array of angle-intensity data pairs contains gaps where the detector overlap regions lie. To circumvent this problem two data sets are collected with the detector array offset to capture data in the gap regions. Angle values in the data at the second position are corrected by the Mythen dector control software to approximately align them with angles from the first dataset. Machining tolerances lead to a systematic uncertainty in the offset angle. The data from an individual capture run from the detector therefore contains gaps and some systematic uncertainty in both the angle and intensity values. PDViPeR can merge the two datasets to produce a single contiguous dataset by normalising and offsetting the data, discarding poor data points near the gap edges, and combining all remaining data points or substituting data points from a dataset acquired at the second position that cover the angle range of the gap region of the first position. We call the process of combining all the data points *merging* and that of substituting data in the gap regions *splicing*. Finally, PDViPeR can concatenate data from two overlapping 80 |degree| ranges to produce a dataset with extended range.

* Datasets are merged in pairs
* Each file in the pair is obtained from roughly the same angular range, with the Mythen detector rotated slightly to ensure detector photosites align with gaps between photosites

Normalising data
----------------
* Normalisation reference can be a particular position

Regridding data
---------------
* Regrid data at 0.00375 |degree| using linear interpolation 

Saving results
==============
* Writes .xye files named according to the processing steps applied
* logfile.log entry for each file written

Plotting
========
* Plot types available
    * Vertically stacked series
    * Interpolated 2D image
    * 3D waterfall
* logfile.log entry for each plot written
