import numpy as np
from numpy import array, arange, linspace, meshgrid, exp
from xye import XYEDataset
from scipy import interpolate
import scipy.ndimage as sn
import scipy.optimize as so
import matplotlib.pyplot as plt

__doc__ = \
"""
Data processing steps applied to the .xye data series.
One or more XYEDataset data series are read into a datasets collection, referred to as dataset_0..dataset_n-1 here.
dataset_0 is treated as the reference set for zero correction and normalisation operations - that is, it is left unchanged.
The following order of operations is followed:

Step 1.
"Zero correction" is applied.
The detector angle has an uncertainty of the order of 0.001 degree between acquisition runs so that I vs 2theta
curves will be misaligned with each other.
This correction will try to shift the datasets dataset_1.._n-1 along the 2theta axis to ensure all peaks are aligned.
A peak detection algorithm will try to identify the largest peak in each series by fitting a linear combination of a
Gaussian+Lorentzian to the peaks. Alternatively we can ask the user to select an angle range using the GUI within which a
peak lies that can be used for alignment purposes.
Once the peak is fitted the series will be interpolated using spline interpolation and the centre location used to resample
the series at the offset sample locations.
Not all data sets contain peaks that can be used for alignment purposes. In such cases, no alignment should be attempted.
A GUI checkbox will be provided to allow enabling/disabling of this step.

Steps 2-4.
All the data series have approximately 0.5deg gaps in the data for angles not covered by the detector array.
To overcome this, multiple data series are captured and merged, with the detector offset by different angles.

Step 2.
"Identify gaps."
To merge the data from multiple offsets of the detector array, first the 5 samples on each side of the gap are discarded.
The gap is identified by taking the difference in 2theta value between adjacent samples. Samples are usually spaced by
about 0.00375deg, except at gaps where the spacing is about 0.5 deg.

Step 3.
"Normalise data."
The scaler1.S8 value in the .parab file contains the incoming beam intensity.
The intensity values of dataset_1.._n-1 are rescaled according to the incoming beam intensity for that data series to an
incoming beam intensity equal to that for dataset_0. i.e. all values in dataset n are multiplied by
.parab_0_scaler1.S8/.parab_n_scaler1.S8.
Problems in capturing data can result in datasets containing all zeros. This condition should be identified and an
error message displayed to the uesr.

Step 4.
"Merge data" or "Splice data".
To combine the overlapping data, the data points are combined and sorted in order of increasing angle. An interpolation
spline is then fitted to the data and the data is resampled every 0.00375deg.

Step 5.
The data is output as an .xye file along with a .parab file.
A GUI checkbox option enables the .parab file contents to be prepended to the .xye file.
"""

import exceptions

class FitFailed(exceptions.Exception):
    def __str__(self):
        print "","Peak fit failed"


def cubic_interpolate(x, y, z, x_size, y_size):
    """
    This 2D interpolation routine is used by the 2D surface plot to generate values between actual plot series data values.
    """
    xsi = linspace(np.min(x), np.max(x), x_size)
    ysi = linspace(1, y.shape[0], y_size)
    xi, yi = meshgrid(xsi, ysi)
    zi = interpolate.griddata((x.ravel(), y.ravel()), z.ravel(), (xi, yi), method='cubic')
    return xi, yi, zi


def bin_data(data, num_bins):
    binned_y = []
    x = data[:,:,0]
    xs = linspace(np.min(x), np.max(x), num_bins + 1)
    # Make sure the maximum point falls inside the last bin
    xs[-1] += 1
    for dataset in data:
        x, y = dataset.T
        bin_indexes = np.digitize(x, xs)
        binned_y.append([ y[bin_indexes == i] for i in range(1, len(xs)) ])

    max_y = np.vstack([ array([ bin.max() if len(bin) > 0 else 0.0 for bin in y ]) for y in binned_y ])
    xsb = linspace(np.min(x), np.max(x), num_bins)
    ysb = linspace(1, max_y.shape[0], max_y.shape[0])
    x, y = meshgrid(xsb, ysb)
    return x, y, max_y


def stack_datasets(datasets):
    #normalise_datasets(datasets)
    shapes = [ len(dataset.data) for name, dataset in datasets.iteritems() ]
    min_x_len = np.min(shapes)
    data = [ dataset.data[:min_x_len] for name, dataset in datasets.iteritems() ]
    stack = np.vstack([data])
    return stack


def interpolate_datasets(datasets, points):
    """
    1D interplotation using scipy's wrapper of fitpack http://www.netlib.org/dierckx/
    According to the IDL reference guide, IDL's SPLINE function performs cubic spline interpolation.
    The call signature is Result = SPLINE( X, Y, T [, Sigma] [, /DOUBLE] )
    A typical call to the SPLINE routine in the IDL version of DataPro is
    spline(splicedata(0,*), splicedata(1,*), step, 15, /double)
    showing that Sigma=15
    From the IDL docs, "Sigma is the amount of 'tension' that is applied to the curve.
    The default value is 1.0. If sigma is close to 0, (e.g., .01), then effectively there is a
    cubic spline fit. If sigma is large, (e.g., greater than 10), then the fit will be like a
    polynomial interpolation."
    Here we replace the IDL method by scipy's closest equivalent:
    http://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html#scipy.interpolate.griddata
    """
    x = datasets[:,:,0]
    y = datasets[:,:,1]
    x_min = x.min(axis=1).max()
    x_max = x.max(axis=1).min()
    x_index = np.linspace(x_min, x_max, points)
    y_data = None
    for x_row, y_row in zip(x, y):
        tck = interpolate.splrep(x_row, y_row, s=0, k=3)
        y_new = interpolate.splev(x_index, tck, der=0)
        if y_data is None:
            y_data = array([y_new])
        else:
            y_data = np.vstack([y_data , y_new])
    return (x_index, y_data)


def rescale(data, method='log'):
    if method == 'log':
        new_data = np.log(data)
    elif method == 'sqrt':
        new_data = np.sqrt(data)
    else:
        new_data = data
    return new_data


def fill_gaps(dataset, method='merge'):
    filename = dataset.source
    if '_p1_' not in filename:
        return dataset.data
    p2_filename = filename.replace('_p1_', '_p2_')
    try:
        disabled
        p2 = XYEDataset.from_file(p2_filename)
        key = 'Integrated Ion Chamber Count(counts)'
        p2_count = p2.metadata[key]
        p1_count = dataset.metadata[key]
        p2.data[:,1] *= p1_count / p2_count
        dataset.data = combine_by_merge(dataset, p2)
    except:
        pass
    return dataset.data


def combine_by_merge(d1, d2):
    combined = np.vstack([d1.data, d2.data])
    indices = combined[:,0].argsort()
    new_data = combined[indices]
    x, y = np.transpose(new_data)
    # Remove duplicate x values that interfere with interpolation
    x_diff = np.diff(x)
    # Don't forget the first element, which doesn't have a diff result yet
    x_diff = np.r_[1, x_diff]
    # Only take the unique values from the array
    x_uniq = x_diff > 0
    return new_data[x_uniq]


def normalise_datasets(datasets):
    key = 'Integrated Ion Chamber Count(counts)'
    counts = array([ dataset.metadata[key] for dataset in datasets.values() ])
    max_count = counts.max()
    for dataset in datasets.values():
        dataset.data[:,1] *= max_count / dataset.metadata[key]


def fit_peak_2theta(data_x, data_y, plot=False):
    """
    Returns the 2theta value of the 1st moment/mean of a peak lying in the provided
    data according to a maximum likelihood fit of a linear combination of a
    Gaussian+Lorentzian. Assumes any background has been removed prior to calling and
    the data is assumed to contain just a single peak to be fitted.
    <data_x> is a 1D array containing the 2theta values
    <data_y> is a 1D array containing the intensity values

    If fitting is successful, the  central x value of the peak is returned.
    If unsuccessful, a FitFailed exception is raised.

    Note, scipy v0.11 has a wavelet-based peak finding function
    scipy.signal.find_peaks_cwt which should do a much better job than the approach
    taken here according to http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2631518/.
    """
    # smooth the ys (Intensities) a bit by using ndimage grey_opening then subtract off the background
    foreground_ys = sn.grey_opening(data_y, size=(2,), mode='nearest')
    # choose a threshold of 1/10 of the height of the biggest sample in the filtered and backgrounded data
    y_threshold = foreground_ys.max()/10.0
    # Get the range exceeding the threshold and use the centre and width as a starting point for
    # a Gaussian+Lorentzian fit
    zero_crossing_indices = np.where(np.diff(np.sign(data_y > y_threshold)))[0] # indices of threshold crossings
    assert zero_crossing_indices.size == 2             # verify we have only two zero crossings
    peak_nearby_index = zero_crossing_indices.mean().round().astype(int) # rough index of the peak centre
    # peaks lie in the middle of the zero crossing pairs - get these positions
    x_peak_candidate_centre = data_x[zero_crossing_indices].mean()
    x_peak_candidate_width = np.diff(data_x[zero_crossing_indices]) / 2.0

    # Gaussian + Lorentzian function - both centred around p[1]
    # p[0] and p[3] are the amplitudes of the respective components
    # p[2] and p[4] are the fit parameters of the respective functions
    fit_function = lambda p, x: p[0]*exp(-((x-p[1])/p[2])**2/2.0) + \
                                p[3]*(p[4]**2/((x-p[1])**2 + p[4]**2))
    fit_function_error = lambda p, x, y: (fit_function(p,x) - y)    # 1d Gaussian + Lorentzian fit

    p0 = np.r_[data_y[peak_nearby_index]/2.0,
               x_peak_candidate_centre,
               x_peak_candidate_width,
               data_y[peak_nearby_index]/2.0,
               x_peak_candidate_width]
    p, success = so.leastsq(fit_function_error, p0[:],
                 args=(data_x, foreground_ys))

    if not success:
        raise FitFailed

    if plot:
        plt.plot(data_x, foreground_ys)
        x_samples = np.linspace(data_x[0], data_x[-1], 1000)
        plt.plot(x_samples, fit_function(p, x_samples))
        plt.show()

    return p[1]


def fit_peaks_2theta(dataset, low_index=None, high_index=None, plot=False):
    """
    Returns the 2theta value of the 1st moment/mean of several peaks according
    to a maximum likelihood fit of a linear combination of a Gaussian+Lorentzian.
    <dataset> is an XYEDataset instance
    <low_index> and <high_index> if provided constrain the search range
    The data is filtered by a windowing filter in order to ignore any rogue samples
    due to noise.
    A threshold is then applied to locate candidate peaks.
    A fit is attempted on the highest peak.
    If successful, the central x value of each peak is returned.
    If any peaks are not fitted, a FitFailed exception is raised.

    Note, scipy v0.11 has a wavelet-based peak finding function
    scipy.signal.find_peaks_cwt which should do a much better job than the approach
    taken here according to http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2631518/.
    """
    data_x = dataset.x()
    data_y = dataset.y()
    # Get the baseline by using a median filter about 3x as long as the widest anticipated peak width
    y_baseline = sn.filters.median_filter(data_y, size=(500,), mode='nearest')
    # smooth the ys (Intensities) a bit by using ndimage grey_opening then subtract off the background
    foreground_ys = sn.grey_opening(data_y, size=(2,), mode='nearest') - y_baseline
    # choose a threshold of 1/10 of the height of the biggest peak in the filtered and backgrounded data
    y_threshold = foreground_ys.max()/10.0
    # Get the ranges exceeding the threshold and use their centres and widths as starting points for
    # Gaussian+Lorentzian fits
    zero_crossing_indices = np.where(np.diff(np.sign(data_y > y_threshold)))[0] # indices of threshold crossings
    assert zero_crossing_indices.size&1 == 0             # verify we have an even number of zero crossings
    peak_nearby_indices = zero_crossing_indices.reshape(-1, 2).mean(axis=1).round().astype(int) # rough indices of peak centres
    # peaks lie in the middle of the zero crossing pairs - get these positions
    x_peak_candidate_centres = data_x[zero_crossing_indices].reshape(-1, 2).mean(axis=1)
    x_peak_candidate_widths = np.diff(data_x[zero_crossing_indices].reshape(-1, 2), axis=1) / 2.0

    # Gaussian + Lorentzian function - both centred around p[1]
    # p[0] and p[3] are the amplitudes of the respective components
    # p[2] and p[4] are the fit parameters of the respective functions
    fit_function = lambda p, x: p[0]*exp(-((x-p[1])/p[2])**2/2.0) + \
                                p[3]*(p[4]**2/((x-p[1])**2 + p[4]**2))
    fit_function_error = lambda p, x, y: (fit_function(p,x) - y)    # 1d Gaussian + Lorentzian fit

    ps = []
    at_least_one_successful_fit = False
    for i in range(x_peak_candidate_centres.size):
        low, high = zero_crossing_indices.reshape(-1, 2)[i]
        # expand the index range to cover the peak and tails
        width_multiplier = 3
        peak_index_low = low - (high-low)*width_multiplier
        peak_index_high = high + (high-low)*width_multiplier
        peak_index_range = arange(peak_index_low, peak_index_high+1)
    
        p0 = np.r_[data_y[peak_nearby_indices[i]]/2.0,
                   x_peak_candidate_centres[i],
                   x_peak_candidate_widths[i],
                   data_y[peak_nearby_indices[i]]/2.0,
                   x_peak_candidate_widths[i]]
        p, success = so.leastsq(fit_function_error, p0[:],
                     args=(data_x[peak_index_range], foreground_ys[peak_index_range]))
        if success:
            at_least_one_successful_fit = True
            ps.append(p[1])
        else:
            ps.append(None)

        if plot:
            plt.plot(data_x[peak_index_range], foreground_ys[peak_index_range])
            x_samples = np.linspace(data_x[peak_index_range][0], data_x[peak_index_range][-1], 1000)
            plt.plot(x_samples, fit_function(p, x_samples))

        if not at_least_one_successful_fit:
            raise FitFailed

    if plot:
        plt.show()

    return ps