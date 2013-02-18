from os import path
from copy import deepcopy
import re
from functools import cmp_to_key

import numpy as np
from numpy import array, linspace, meshgrid, exp
from scipy import interpolate
import scipy.ndimage as sn
import scipy.optimize as so
import matplotlib.pyplot as plt

from xye import XYEDataset

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
The intensity values of dataset_1.._n-1 are rescaled according to the incoming beam intensity for that data series to the
incoming beam intensity of a selected reference dataset_r. i.e. all values in dataset n are multiplied by
.parab_r_scaler1.S8/.parab_n_scaler1.S8.
Problems in capturing data can result in datasets containing all zeros. This condition should be identified and an
error message displayed to the user.

Step 4.
"Merge data" or "Splice data".
To combine the overlapping data, the data points are combined and sorted in order of increasing angle. An interpolation
spline is then fitted to the data and the data is resampled every 0.00375deg.

Step 5.
The data is output as an .xye file along with a .parab file.
A GUI checkbox option enables the .parab file contents to be prepended to the .xye file.
"""

class DatasetProcessor(object):
    def __init__(self, normalise=True, correction=0.0, align_positions=True,
                 merge_by_splice=True, merge_by_merge=True, regrid=False,
                 normalisation_reference=True, datasets=True):
        self.normalise = normalise
        self.correction = correction
        self.align_positions = align_positions
        self.merge_by_splice = merge_by_splice
        self.merge_by_merge = merge_by_merge
        self.regrid = regrid
        self.normalisation_reference = normalisation_reference
        self.datasets = datasets


    def process_dataset(self, dataset):
        # trim data from gap edges prior to merging
        dataset = dataset.copy()
        dataset.data = clean_gaps(dataset.data)
        return dataset


    def process_dataset_pair(self, dataset_pair):
        dataset_pair = map(lambda d: d.copy(), dataset_pair)
        dataset1, dataset2 = dataset_pair

        # normalise
        if self.normalise:
            dataset1 = self.normalise_me(dataset1)
            dataset2 = self.normalise_me(dataset2)

        # trim data from gap edges prior to merging
        dataset1.data = clean_gaps(dataset1.data)
        dataset2.data = clean_gaps(dataset2.data)

        # zero correct i.e. shift x values
        if self.correction != 0.0:
            dataset1.data[:,0] += self.correction
            dataset2.data[:,0] += self.correction

        if self.align_positions:
            if 'peak_fit' in dataset1.metadata and \
               'peak_fit' in dataset2.metadata:
                x_offset = dataset1.metadata['peak_fit'] - \
                            dataset2.metadata['peak_fit']
                dataset2.data[:,0] += x_offset

        # merge and/or splice
        if self.merge_by_splice and self.merge_by_merge:
            spliced_datasets = self._merge_datasets(dataset1, dataset2, 'splice')
            merged_datasets = self._merge_datasets(dataset1, dataset2, 'merge')
            merged_datasets = merged_datasets + spliced_datasets
        elif self.merge_by_splice:
            merged_datasets = self._merge_datasets(dataset1, dataset2, 'splice')
        elif self.merge_by_merge:
            merged_datasets = self._merge_datasets(dataset1, dataset2, 'merge')
        else:
            merged_datasets = []

        # regrid
        if self.regrid:
            regridded_datasets = []
            for dataset in merged_datasets:
                regridded_datasets.append(self.regrid_me(dataset))
            merged_datasets.extend(regridded_datasets)
        return merged_datasets


    def normalise_me(self, dataset):
        if self.normalise:
            dataset1 = dataset.copy()
            try:
                datasets_dict = dict([(d.name, d) for d in self.datasets])
                if self.normalisation_reference in ['p1', 'p2', 'p3', 'p4']:
                    # Normalise to selected position
                    selected_filebase = re.sub('_p[1-4]*_',
                                               '_{}_'.format(self.normalisation_reference),
                                               dataset1.name)
                    nr_dataset = datasets_dict[selected_filebase]
                else:
                    # Normalise to selected file
                    nr_dataset = datasets_dict[self.normalisation_reference]
                dataset1.data = normalise_dataset([nr_dataset, dataset1])
                dataset1.name = insert_descriptor(dataset1.name, 'n')
                return dataset1
            except:
                pass
        return None


    def regrid_me(self, dataset):
        if self.regrid:
            dataset1 = dataset.copy()
            dataset1.data = regrid_data(dataset1.data)
            dataset1.name = insert_descriptor(dataset1.name, 'g')
            return dataset1
        return None


    def _merge_datasets(self, dataset1, dataset2, merge_method):
        if merge_method == 'merge':
            merged_data = combine_by_merge(dataset1.data, dataset2.data)
            merge_label = 'm'
        elif merge_method == 'splice':
            merged_data = combine_by_splice(dataset1.data, dataset2.data)
            merge_label = 's'
        else:
            raise ValueError('Merge method not understood')

        # Create a new dataset to store the merged data in.
        current_directory = path.abspath(dataset1.source)
        merged_data_filebase = dataset1.name.replace('_p12_', '_p1234_')\
                                       .replace('_p1_', '_p12_')\
                                       .replace('_p3_', '_p34_')
        merged_data_filebase = insert_descriptor(merged_data_filebase, merge_label)
        merged_data_filename = path.join(current_directory, merged_data_filebase)
        merged_dataset = XYEDataset(merged_data, merged_data_filebase,
                                          merged_data_filename,
                                          deepcopy(dataset1.metadata))
        return [merged_dataset]


    def splice_overlapping_datasets(self, datasets):
        dataset1, dataset2 = datasets
        merged_data = splice_overlapping_data(dataset1.data, dataset2.data)
    
        # Create a new dataset to store the merged data in.
        current_directory = path.abspath(dataset1.source)
        merged_data_filebase = re.sub('(_p[1-4]*_)',
                                      r'_p1234_',
                                      dataset1.name)
        merged_data_filebase = insert_descriptor(merged_data_filebase, 's')
        merged_data_filename = path.join(current_directory, merged_data_filebase)
        merged_dataset = XYEDataset(merged_data, merged_data_filebase,
                                          merged_data_filename,
                                          deepcopy(dataset1.metadata))
        return [merged_dataset]


def insert_descriptor(filename, insertion):
    '''
    Makes a new filename based on the existing one.
    A filename is of the form
    foo_[nnnn].xye, foo_[nnnn].xy, foo_[descriptor]_[nnnn].xy, or foo_[descriptor]_[nnnn].xye where
    [nnnn] is a 4-digit sequence id, and
    [descriptor] is a code string that describes the processing that has been performed, where the code
    may only contain characters from the ordered list ['n','s','m','g','b','t'] which, if included, will be
    in the order shown.
    The insertion string may be a character or character combination from the list, which is inserted
    into the descriptor.
    For filenames without a descriptor, one is created.
    For filenames of form foo.ext returns foo_[descriptor].ext
    '''
    parts = filename.split('_')
    if len(parts) == 1:
        # filename of form foo.ext - return foo_[descriptor].ext
        fname, ext = parts[0].split('.')
        return '{}_{}.{}'.format(fname, insertion, ext)
    regex = r'^(n?s?m?g?b?t?)$'
    match = re.match(regex, parts[-2])      # check if 2nd last group is a descriptor     
    if match is not None:
        # descriptor found, so insert the new insertion at the appropriate location
        order = ['n','s','m','g','b','t']       # sort order for characters in descriptor group
        # tuple(match_string) -> match_string -> match_string+insertion_string -> sorted string based on order
        descriptor = match.groups()[0]
        if insertion != descriptor:
            new_descriptor = ''.join(sorted(list(descriptor + insertion),
                                    key=cmp_to_key(lambda x,y: order.index(x)-order.index(y))))
            return '_'.join(parts[:-2] + [new_descriptor] + parts[-1:])
        else:
             return  '_'.join(parts[:-2] + [descriptor] + parts[-1:])
    else:
        # no descriptor found, so insert a new one
        return '_'.join(parts[:-1] + [insertion] + parts[-1:])


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
        x, y, e = dataset.T
        bin_indexes = np.digitize(x, xs)
        binned_y.append([ y[bin_indexes == i] for i in range(1, len(xs)) ])

    max_y = np.vstack([ array([ bin.max() if len(bin) > 0 else 0.0 for bin in y ]) for y in binned_y ])
    xsb = linspace(np.min(x), np.max(x), num_bins)
    ysb = linspace(1, max_y.shape[0], max_y.shape[0])
    x, y = meshgrid(xsb, ysb)
    return x, y, max_y


def stack_datasets(datasets):
    """ This is called by the plotting routines so we only collect those data series that
    are set to active in the dataset editor
    """
    shapes = [ len(dataset.data) for dataset in datasets if dataset.metadata['ui'].active]
    min_x_len = np.min(shapes)
    data = [ dataset.data[:min_x_len] for dataset in datasets if dataset.metadata['ui'].active ]

    stack = np.vstack([data])
    return stack


def interpolate_datasets(datasets, points):
    """
    Regrid data onto a regular grid of n=points x-values.
    """
    x = datasets[:,:,0]
    y = datasets[:,:,1]
    flipped = False
    if x[0,0] > x[0,-1]:
        # x's are in descending order, spline interplotaion assumes ascending order,
        # so flip all data along x and unflip it after interpolating
        x = x[:,::-1]
        y = y[:,::-1]
        flipped = True

    x_min = x.min(axis=1).max()
    x_max = x.max(axis=1).min()
    x_index = np.linspace(x_min, x_max, points)
    y_data = None
    for x_row, y_row in zip(x, y):
        tck = interpolate.splrep(x_row, y_row, s=0, k=1)
        y_new = interpolate.splev(x_index, tck, der=0)
        if y_data is None:
            y_data = array([y_new])
        else:
            y_data = np.vstack([y_data , y_new])
    if flipped:
        x_index = x_index[::-1]
        y_data = y_data[:,::-1]
    return (x_index, y_data)


def rescale(data, method='log'):
    if method == 'log':
        new_data = np.log(data)
    elif method == 'sqrt':
        new_data = np.sqrt(data)
    else:
        new_data = data
    return new_data


def clean_gaps(data, gap_threshold=0.1, shave_number=5):
    """
    data is an Nx2 array of xy data.
    Gaps in the detector array lead to gaps in the data and corruption of the sample
    values adjacent to the gaps. Therefore this routine is called prior to merging the
    data for the two detector positions to remove 5 (currently) samples from each side of
    the identified gaps.
    """
    # Gaps are 0.5 deg each whereas data points are typically spaced by about 0.00375 deg
    gap_indices = np.where(np.diff(data[:,0]) > gap_threshold)[0]
    # Now gap_indices contains indices of samples on the LHS of the gap
    # Expand indices into ranges +/- shave_number
    deletion_indices = gap_indices[np.newaxis].T + np.arange(1-shave_number, 1+shave_number)
    return np.delete(data, deletion_indices, axis=0)


def combine_by_merge(d1, d2):
    """
    d1 and d2 are Nx3 arrays of xye data.
    Merge the datasets by combining all data points in x-sorted order.
    Assumes that the 'gaps' in d1 have been cleaned by a call to clean_gaps().
    If any points have exactly duplicated x values the d2 point is not merged.
    """
    combined = np.vstack([d1, d2])
    indices = combined[:,0].argsort()
    new_data = combined[indices]
    x = new_data[:,0]
    # Remove duplicate x values that interfere with interpolation
    x_diff = np.diff(x)
    # Don't forget the first element, which doesn't have a diff result yet
    x_diff = np.r_[1, x_diff]
    # Only take the unique values from the array
    x_uniq = x_diff > 0
    return new_data[x_uniq]


def combine_by_splice(d1, d2, gap_threshold=0.1):
    """
    d1 and d2 are Nx3 arrays of xye data.
    Replace the 'gaps' in d1 by valid data in the corresponding parts of d2.
    Assumes that the 'gaps' in d1 have been cleaned by a call to clean_gaps().
    """
    # Identify the gaps in d1
    gap_indices = np.where(np.diff(d1[:,0]) > gap_threshold)[0]
    # get the x or 2theta value ranges for the samples at the edges of the gaps in d1
    x_edges = np.c_[d1[:,0][gap_indices], d1[:,0][gap_indices + 1]]
    # for each identified gap in d1, insert that segment from d2
    d1 = d1[:]
    for lower, upper in x_edges:
        new_segment = d2[(d2[:,0] > lower) & (d2[:,0] < upper)]
        d1 = combine_by_merge(d1, new_segment)
    return d1


def splice_overlapping_data(d1, d2):
    """
    d1 and d2 are Nx3 arrays of xye data.
    d1 is assumed to cover an angular range starting below that of d2 so we trim
    shave_number samples off the RHS of d1 before concatenating d2 to it starting at the
    next highest value of 2theta.
    """
    # Identify cut index in d2
    # Concatenate d1 and d2
    right = d2[d2[:,0]>d1[-1,0]]
    return np.vstack((d1, right))


def regrid_data(data, start=None, end=None, interval=0.00375):
    """
    data is an Nx3 array of xye data.
    Returns an Nx3 array of the data resampled at x values starting at start and
    spaced by interval.
    If start==None the start x value is the first x value in the input data.
    If end==None the end x value is the last value less than or equal to the last
    x value in the input data.
    """
    data = np.cast[np.double](data)

    # Looking at the behaviour of the existing IDL code which uses the spline() fitting function with
    # sigma=15 and speaking to Qinfen, linear interpolation will probably work just as well and is extremely fast.
    # If linear interpolation is no good, the two best options appear to be InterpolatedUnivariateSpline and pchip.
    # pchip works beautifully but unfortunately is slow as it has to compute a Hermite polynomial between each data point.
    # Unfortunately it is probably too slow for processing large numbers of datasets.
    # The KroghInterpolator and BarycentricInterpolator don't work properly on my test data - it is too big and ill-conditioned.
    # The LSQUnivariateSpline is not useful for close fitting of large data.
    # Uncomment one of the following methods:
    # y_interpolator = interpolate.InterpolatedUnivariateSpline(data[:,0], data[:,1], k=5)
    # y_interpolator = interpolate.pchip(data[:,0], data[:,1])
    # y_interpolator = interpolate.interp1d(data[:,0], data[:,1], kind='quadratic')         # worse than linear InterpolatedUnivariateSpline
    # y_interpolator = interpolate.interp1d(data[:,0], data[:,1], kind='cubic')             # OK, as expected, but not as close at the 
    # y_interpolator = interpolate.interp1d(data[:,0], data[:,1], kind='nearest')           # probably unacceptable?
    y_interpolator = lambda xs: np.interp(xs, data[:,0], data[:,1])                         # linear interpolation

    # e_interpolator = interpolate.InterpolatedUnivariateSpline(data[:,0], data[:,2], k=5)
    # e_interpolator = interpolate.pchip(data[:,0], data[:,2])
    # e_interpolator = interpolate.interp1d(data[:,0], data[:,2], kind='quadratic')         # worse than linear InterpolatedUnivariateSpline
    # e_interpolator = interpolate.interp1d(data[:,0], data[:,2], kind='cubic')             # OK, as expected, but not as close at the 
    # e_interpolator = interpolate.interp1d(data[:,0], data[:,2], kind='nearest')           # probably unacceptable?
    e_interpolator = lambda xs: np.interp(xs, data[:,0], data[:,2])                         # linear interpolation

    flipped = False
    if data[0,0] > data[-1,0]:
        # x's are in descending order, spline interplotaion assumes ascending order,
        # so flip all data along x and unflip it after interpolating
        data = data[::-1]
        flipped = True
    if start==None:
        start = data[0,0]
    if end==None:
        end = data[-1,0]
    xs = np.arange(start, end+interval/100.0, interval)
    new_data = np.c_[xs, y_interpolator(xs), e_interpolator(xs)]
    if flipped:
        new_data = new_data[::-1]
    return new_data


def normalise_dataset(dataset_pair):
    """
    For a pair of datasets, normalise the y-values of the second dataset with respect
    to the first, based on the measured beam intensity.
    """
    dataset1, dataset2 = dataset_pair
    key = 'Integrated Ion Chamber Count(counts)'
    data = dataset2.data.copy()
    if dataset1.name != dataset2.name:
        data[:,1] *= dataset1.metadata[key] / dataset2.metadata[key]            # renormalise y-value
        data[:,2] *= np.sqrt(dataset1.metadata[key] / dataset2.metadata[key])   # renormalise uncertainty
    return data


def get_peak_offsets_for_all_dataseries(range_low, range_high, datasets):
    """
    Perform peak detection for every dataset within the defined range.
    If successful, the fit result is appended to the XYEDataset item metadata.
    The fit result can be a float or None in the case of a series that could not be fitted.
    """
    for dataset in datasets:
        x_range = (dataset.x() >= range_low) & (dataset.x() <= range_high)
        # Get the baseline by using a median filter 3x as long as the selection
        filter_length = 3*int(len(dataset.x())*(range_high-range_low)/(dataset.x()[-1]-dataset.x()[0]))
        # restrict filter length to a sane value
        if filter_length > 10000:               filter_length = 10000
        if filter_length < 20:                  filter_length = 20
        if filter_length > len(dataset.x())/2:  filter_length = len(dataset.x())/2
        y_baseline = sn.filters.median_filter(dataset.y(), size=filter_length, mode='nearest')
        # get just the data in the range defined by the range_low, range_high parameters
        data_x, data_y = dataset.data[x_range][:,:2].T
        data_y_baseline_removed = data_y - y_baseline[x_range]
        fit_centre, _ = fit_peak_2theta(data_x, data_y_baseline_removed)
        dataset.add_param('peak_fit', fit_centre)


def fit_peaks_for_a_dataset_pair(range_low, range_high, dataset_pair, normalise_checked):
    """
    Perform peak detection within the defined range <range_low> to <range_high> for a
    dataset pair. <dataset_pair> is a tuple taken from the MainApp.dataset_pairs set
    container that contains keys into <datasets>.

    The lowest (odd numbered) position is fitted and this fit is used to obtain the offset
    in the pair.
    If successful, the fit result is appended to the XYEDataset item metadata.
    The fit result can be a float or None in the case of a series that could not be fitted.
    Returns True if the peaks were fitted successfully in both positions, else returns False.
    """
    dataset, dataset2 = dataset_pair
    x_range = (dataset.x() >= range_low) & (dataset.x() <= range_high)
    data_x, data_y = dataset.data[x_range][:,:2].T

    # I want to be able to turn on median filtering easily so leave this code here for now.
    # Fit the first position dataset.
    enable_filter = False
    if enable_filter:
        # Get the baseline by using a median filter 3x as long as the selection
        filter_length = 3*int(len(dataset.x())*(range_high-range_low)/(dataset.x()[-1]-dataset.x()[0]))
        # restrict filter length to a sane value
        if filter_length > 10000:               filter_length = 10000
        if filter_length < 20:                  filter_length = 20
        if filter_length > len(dataset.x())/2:  filter_length = len(dataset.x())/2
        y_baseline = sn.filters.median_filter(dataset.y(), size=filter_length, mode='nearest')
        # get just the data in the range defined by the range_low, range_high parameters
        data_y_baseline_removed = data_y - y_baseline[x_range]
        fit_centre, fit_parameters = fit_peak_2theta(data_x, data_y_baseline_removed)
    else:
        fit_centre, fit_parameters = fit_peak_2theta(data_x, data_y)
    
    # If the fit was successful, fit the second dataset.
    # First dataset was fit successfully, fit the other dataset with the peak fitting result.
    x_range = (dataset2.x() >= range_low) & (dataset2.x() <= range_high)
    data_x, data_y = dataset2.data[x_range][:,:2].T

    # Normalise the second dataset's y values if necessary
    if normalise_checked:
        key = 'Integrated Ion Chamber Count(counts)'
        data_y *= dataset.metadata[key] / dataset2.metadata[key]

    fit2_centre, fit2_successful = fit_modeled_peak_to_data(data_x, data_y, fit_parameters)
    # Store the fit results if both data series were successfully fitted.
    if fit2_successful:
        dataset.add_param('peak_fit', fit_centre)
        dataset2.add_param('peak_fit', fit2_centre)
    return fit2_successful


def fit_peak_2theta(data_x, data_y, plot=False):
    """
    Fits a linear combination of a Gaussian+Lorentzian+Constant to the specified data.
    The data is assumed to contain just a single peak to be fitted.
    <data_x> is a 1D array containing the 2theta values.
    <data_y> is a 1D array containing the intensity values.
    <plot> is a debug hook for generating a matplotlib plot window showing the fit.
    Returns a tuple containing two items:
    The first item is the 2theta value of the higher of the gaussian or lorentzian peak
    and the second item is the list of all parameters found by the fitting algorithm.

    Note, scipy v0.11 has a wavelet-based peak finding function
    scipy.signal.find_peaks_cwt which should do a much better job than the approach
    taken here according to http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2631518/.
    """
#    # smooth the ys (Intensities) a bit by using ndimage grey_opening then subtract off the background
#    foreground_ys = sn.grey_opening(data_y, size=(2,), mode='nearest')
    foreground_ys = data_y
    # get the centre and width based on the extrema of the data_x series as a starting
    # point for a Gaussian+Lorentzian fit
    x_peak_candidate_centre = (data_x[0] + data_x[-1])/2.0
    x_peak_candidate_width = (data_x[-1] - data_x[0])/2.0
    peak_height = data_y.max() - data_y.min()

    # Gaussian+Lorentzian+Constant function
    # p[0] and p[3] are the amplitudes of the respective components
    # p[1] and p[4] are the centres of the respective functions
    # p[2] and p[5] are the fit parameters of the respective functions
    # p[6] is a flat background
    fit_function = lambda p, x: p[0]*exp(-((x-p[1])/p[2])**2/2.0) + \
                                p[3]*(p[5]**2/((x-p[4])**2 + p[5]**2)) + p[6]
    fit_function_error = lambda p, x, y: np.linalg.norm(fit_function(p,x) - y)

    p0 = np.r_[peak_height/2.0,
               x_peak_candidate_centre,
               x_peak_candidate_width,
               peak_height/2.0,
               x_peak_candidate_centre,
               x_peak_candidate_width,
               data_y.min()]

    # Use a constraint-based optimisation to ensure that the gaussian and lorentzian are
    # always positive and their widths are reasonable.
    bounds = [(0.0, 1.2*peak_height),   # gaussian height is +ve but limited
              (data_x[0], data_x[-1]),  # gaussian centre lies within the selection
              (x_peak_candidate_width/10, 10*x_peak_candidate_width), # gaussian width is +ve but not too wide
              (0.0, 1.2*peak_height),   # lorentzian height is +ve but limited
              (data_x[0], data_x[-1]),  # lorentzian centre lies within the selection
              (x_peak_candidate_width/10, 6*x_peak_candidate_width), # lorentzian width is +ve but not too wide
              (0.0, data_y.max())]      # constant background is +ve but below the peak max 
    # Fit the data: there's no real way to set a convergence criterion here so always assume convergence.
    # epsilon (the finite difference approximation for fprime) is set to 1/1000th of the selection width.
    # Setting epsilon to 1/100th also seems to work fine, but 1000th seems a safer bet.
    p, _, _ = so.fmin_tnc(fit_function_error, p0[:], args=(data_x, foreground_ys),
                                approx_grad=True, bounds=bounds,
                                epsilon=(data_x[-1]-data_x[0])/1000, disp=0, maxfun=1000)

    if plot:
        plt.plot(data_x, foreground_ys)
        x_samples = np.linspace(data_x[0], data_x[-1], 1000)
        plt.plot(x_samples, fit_function(p, x_samples))
        plt.show()

    return (p[1] if p[0] > p[3] else p[4], p)


def fit_modeled_peak_to_data(data_x, data_y, p0, plot=False):
    """
    Fits a linear combination of a Gaussian+Lorentzian to the specified data allowing only
    the x-location to change.
    The data is assumed to contain a single peak similar in shape to that from which the
    fit parameters were obtained.
    <data_x> is a 1D array containing the 2theta values.
    <data_y> is a 1D array containing the intensity values.
    <plot> is a debug hook for generating a matplotlib plot window showing the fit.
    p0 is the 6-element parameter list:
    # p0[0] and p0[3] are the amplitudes of the respective components
    # p0[1] and p0[4] are the centres of the respective functions
    # p0[2] and p0[5] are the fit parameters of the respective functions
    # p0[6] is a flat background
    Returns a tuple containing two items.
    The second item is the success of the peak fitting (True=success, False=failure).
    If the fit is successful the first item is the 2theta value of the higher of the
    Gaussian or Lorentzian peak.
    Since there is only one free parameter here, I should really use a different fitter
    which would be faster, but this is fast enough.
    """
#    # smooth the ys (Intensities) a bit by using ndimage grey_opening then subtract off the background
#    foreground_ys = sn.grey_opening(data_y, size=(2,), mode='nearest')
    foreground_ys = data_y

    # Gaussian+Lorentzian+Constant function offset by x_offset[0]
    fit_function = lambda x_offset, x: p0[0]*exp(-((x-p0[1]-x_offset[0])/p0[2])**2/2.0) + \
                                p0[3]*(p0[5]**2/((x-p0[4]-x_offset[0])**2 + p0[5]**2)) + p0[6]
    fit_function_error = lambda p, x, y: (fit_function(p,x) - y)    # 1d Gaussian + Lorentzian fit

    x_offset0 = [0.0]
    x_offset, success = so.leastsq(fit_function_error, x_offset0[:], args=(data_x, foreground_ys))

    if plot and success==1:
        plt.plot(data_x, foreground_ys)
        x_samples = np.linspace(data_x[0], data_x[-1], 1000)
        plt.plot(x_samples, fit_function(x_offset, x_samples))
        plt.show()

    return (p0[1]+x_offset[0] if p0[0] > p0[3] else p0[4]+x_offset[0], success==1)


def rebin_preserving_peaks(a, samples):
    """
    A min- and max-preserving rebinning function, used by the plotting routines to
    represent peaks faithfully in visualisations.
    Reduces the data along the "long" axis to a length equal to twice the closest
    multiple of the number of samples. The reduced data contains alternating values
    representing the minimum and maximum value in each interval over which the 
    data was measured.
    <a> is a 2D array with each row containing a data series.
    <samples> is the desired final number of each of the min and max values in each
    row of the returned 2D array.
    i.e. each row will contain 2x samples values.
    Also returns <truncate_at> which is where the array must be truncated so it
    divides into the desired number of intervals, also allowing for an even number of
    intervals.
    """
    bin_length = a.shape[1]/samples
    truncate_at = a.shape[1] - a.shape[1]%bin_length
    bins = truncate_at/bin_length
    a = a.copy()[:,:truncate_at]                       # truncate columns if necessary
#    a.shape = (a.shape[0], -1, truncate_at/bins)
    a.shape = (a.shape[0], bins, -1)
    mins = a.min(axis=2)
    maxs = a.max(axis=2)
    a = np.dstack((mins,maxs)).reshape(a.shape[0],-1)
    return a, truncate_at, bins