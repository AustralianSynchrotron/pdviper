.. _how_to_use_root:

*******************
How to use PDViPeR
*******************
PDViPeR is designed in a modular format, which is grouped into different functions. The software has main menu on the left side and main plot window on the right side image :ref:`figure1`.

.. _figure1:
.. figure:: images/figure1.png
   :scale: 50 %
   :alt: Figure 1

   Figure 1


.. _read_data:
Read data (view module)
=======================
Click “open files” from main menu and select the file(s) you need read in.
Note: It is assumed that the data is .xye/.xy format, for processing the data from the MYTHEN detector.  The .parab file is required to be located in the same folder as the data file for many of the functions to work. There is a .parab file for each detector position data file.
Click “Edit datasets” from main menu, then Edit datasets window will pop up :ref:`figure2`. In this window you can change the color, markers, marker size, line width, and select/deselect each dataset.

.. _figure2:
.. figure:: images/figure2.png
   :scale: 50 %
   :alt: Figure 2

   Figure 2

Legend, gridlines, and crosslines can be turn off/on from main menu window using the “show legend”, “show gridlines”, “show crosslines” tick boxes. To zoom, unzoom, pan and the drag dataset in the plot window the left, right mouse button, or keyboard arrow can be used. The plot scale can be set to “linear”, “log”, or “sqrt” in the drop-down menu.
Note: you always can click “reset view” bottom to reset plot.
The dataset plot image can be saved via the “Save as image” button located in the main window.
To plot a dataset in “stacked”, “2d surface”, “3d plot” view, click the “generate plot” menu button.  A new plot generator window will be opened, see :ref:`figure3`.

.. _figure3:
.. figure:: images/figure3.png
   :scale: 50 %
   :alt: Figure 3

   Figure 3 

Stacked plot
Adjust “offset” and “value range” to change space between the data sets and intensity of the dataset. Tick “flip order” to change the order of plot from top to bottom or reverse. Change the plot scale by selecting “linear”, “log”, “sqrt” options.
2d surface
Double click the plot axis to change the dataset plot range and label. Drag on the scale bar on the right side of the plot to change plot colour scale, see :ref:`figure4`

.. _figure4:
.. figure:: images/figure4.png
   :scale: 50 %
   :alt: Figure 4

   Figure 4 

3d plot
Adjust “Azimuth” and/or “Elevation” to change the plot view direction, or drag the plot with left-button of mouse, see :ref:`figure5`.  Change the plot label and range in the upper menu.  Quality value should be set as “1”, when the plot view is changed; Quality value should be set as “5”, when plot is output for best resolution.

.. _figure5:
.. figure:: images/figure5.png
   :scale: 50 %
   :alt: Figure 5

   Figure 5 


.. _process_data:
Process module
==============

Merging datasets
----------------
The Mythen detector array on the PD beamline consists of several adjacent strip detectors separated by small gaps, and covering a total angular range of approximately 80°. Consequently, the acquired array of angle-intensity data pairs contains gaps where the detector overlap regions lie. To circumvent this problem two data sets are collected with the detector array offset to capture data in the gap regions. Motor encoder errors may lead to a systematic uncertainty in the offset angle (typically ca. 0.001°). The data from an individual capture run from the detector therefore contains gaps and some systematic uncertainty in both the angle and intensity values. PDViPeR can merge the two datasets to produce a single contiguous dataset by normalising and offsetting the data. The software also discards poor data points near the gap edges, and combining all remaining data points or substituting data points from a dataset acquired at the second position that cover the angle range of the gap region of the first position. We call the process of combining all the data points merging and that of substituting data in the gap regions splicing. Finally, PDViPeR can concatenate data from two overlapping 80° ranges to produce a dataset with extended range :ref:`figure6`.

.. _figure6:
.. figure:: images/figure6.png
   :scale: 50 %
   :alt: Figure 6

   Figure 6 

* Datasets are merged in pairs. Select “Positions to process” according to your dataset, then click “Load partners” to load all detector positions. E.g. P1 and P2.
* If you want to correct any misalignments between detector positions (e.g. P1, P2), tick “align positions”, and click “select peak”, select a single non-overlapping peak from the main plot window (this peak must be exist for all the datasets you want to align). Click “Align”.
* “Zero correction” is used to manually correct known detector 2theta angle error. Default = 0.
* Click “Apply”, and “save” the processed dataset into your desired folder.
* Click “undo” if you want to undo process.

Normalising data
-----------------
If storage ring is in decay mode. The incoming intensity on sample changes with the time. Any of the available datasets can be the reference from which all other datasets are normalised to.  Any particular dataset can be used as the normalisation reference by selecting the appropriate dataset in the “Normalise to:” field.

Regridding data
---------------
This is used to generate equal step size data points. Regrid the data in 0.00375° steps using a linear interpolation by ticking the “grid” option.
           
Note regarding output of grid data:
"""""""""""""""""""""""""""""""""""
In order to output data of constant step size it is necessary to interpolate between data point of one or more data files.  This causes neighbouring data points in the subsequent output to be correlated (because neighbouring points in the output probably arose from interpolating between 2 points in the input, at least one of which is common to both of the output points). This correlation destroys the assumption in least squares refinement that the observations are independent, so strictly speaking it is no longer justifiable to quote the numbers coming out of your refinement (particularly esds).  It is therefore preferable to conduct a multi-histogram refinement.

Saving results
---------------
Writes .xye files named according to the processing steps applied. The convention of processed data name as following:

.. csv-table:: Processed datafile naming conventions
   :header: "label","meaning"
   :widths: 10,30

   "m", "merge"
   "s", "splice"
   "n", "normalized"
   "g", "grid"
   "p12", "position P1 and P2 processed"


A logfile.log entry for each file written

.. _background:

Background module
=================
The current function in the background module allows a previously collected ‘background’ dataset to be subtracted from each ‘real’ dataset
In the “Backgrnd” tab, click “load” to load background file. Click “subtract background” and the software will subtract the background dataset from all the loaded datasets. Click “save” to save processed data.

.. _transforms:


Θ d Q module
=============
This function is designed for users to convert data between different units ( 2theta, Q and d spacing)  Data can also be converted into different wavelengths.
In “transforms” tab, click “convert/scale abscissa” to open the convert window, :ref:`figure7`.

.. _figure7:
.. figure:: images/figure7.png
   :scale: 50 %
   :alt: Figure 7

   Figure 7 
 
Select a single data or multi dataset and type in the original wavelength in the “Modify selected x:” field. Type the target wavelength in the “Target value:” field. Select the desired conversion in “from” “to: menu. Click the “Rescale” button. 

