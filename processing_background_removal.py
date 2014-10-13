import numpy as np
import scipy.ndimage as sn

from numpy.polynomial.polynomial import polyfit, polyval
from scipy import interpolate
from processing import insert_descriptor
import re


__doc__ = \
"""
Routines to remove background.
"""

def subtract_background_from_all_datasets(datasets, background_file, background_manual,fitter):
    processed_datasets = []
    
    def update_metadata(dataset):
        dataset.name = insert_descriptor(dataset.name, 'b')
        dataset.metadata['ui'].name = dataset.name + ' (processed)'
        dataset.metadata['ui'].color = None
    
    # If there is a background file uploaded, use that
    if background_file is not None:
        for d in datasets:
            if background_file is not d:
                # does there need to be s
                dataset=subtract_background_with_file(d,background_file)
                processed_datasets.append(dataset)
                update_metadata(dataset)
    # next check if there is a manually fitted background instead
    elif fitter is not None:
        for d in datasets:
            if d is not background_manual:
                dataset=subtract_background_with_fit(d,fitter)
                processed_datasets.append(dataset)
                update_metadata(dataset)
    else:
        # first check if there is an individual curve fit attached to this dataset 
        for d in datasets:           
            if hasattr(d,'background') and d.background is not None:
                dataset = subtract_background(d, d.background)
                processed_datasets.append(dataset)
                update_metadata(dataset)
        #Next see if there's a background file uploaded and use that
              
    return processed_datasets

def subtract_manual_background_from_all_datasets(datasets, fitter):
    processed_datasets = []
    for d in datasets:
        dataset = subtract_background_with_fit(d, fitter)
        processed_datasets.append(dataset)
        dataset.name = insert_descriptor(dataset.name, 'b')
        dataset.metadata['ui'].name = dataset.name + ' (processed)'
        dataset.metadata['ui'].color = None
    return processed_datasets

def subtract_background(foreground,background):
    """
    use this method for subtracting a background from a foreground where they have the same x datapoints
    This is used where we fit a curve for an individual dataset
    """
    dataset = foreground.copy()
    data = background.data
    xs = dataset.data[:,0]
    ys=np.clip(foreground.data[:,1] - background.data[:,1],0,max(dataset.data[:,1]))
    dataset.data = np.c_[xs, ys, dataset.data[:,2]]
    return dataset

def subtract_background_with_fit(foreground,fitter):
    background_dataset = foreground.copy()  
    ys=np.clip(background_dataset.data[:,1]-fitter.eval_curve(background_dataset.data[:,0]),0,max(background_dataset.data[:,1]))
    #ys=np.clip(ys,0,max(ys)) # truncate neg values to 0
    e_interpolator = lambda xs: np.interp(xs, background_dataset.data[:,0], background_dataset.data[:,2])                         # linear interpolation
    xs = background_dataset.data[:,0]
    background_dataset.data = np.c_[xs, ys, background_dataset.data[:,2] + e_interpolator(background_dataset.data[:,0])]
    return background_dataset

def subtract_background_with_file(foreground, background):
    '''
    Resample background dataset at the same x-values as the forgeround and subtract it,
    returning a new XYE dataset sans background.
    '''
    dataset = foreground.copy()

    data = background.data
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

    xs = dataset.data[:,0]
    ys=np.clip(dataset.data[:,1] - y_interpolator(xs),0,max(dataset.data[:,1]))
    dataset.data = np.c_[xs, ys, dataset.data[:,2] + e_interpolator(xs)]
    return dataset

def get_subtracted_datasets(datasets):
    subtracted_datasets=[]
    for d in datasets:
        if re.search(r'_n?s?m?g?bt?_\d+.xye?',d.name):
            subtracted_datasets.append(d)
    return subtracted_datasets


class CurveFitter:
    def __init__(self, curve_type, deg):
        self.fit_func = {'Spline' : self._fit_spline_to_background,
                         'Polynomial' : self._fit_poly_to_background}[curve_type]
        self.eval_func = {'Spline' : self._eval_spline_at_xs,
                          'Polynomial' : self._eval_poly_at_xs}[curve_type]
        self.deg = deg
        self.min_filter_length = 100 
        self.numpoints=curve_type

    def fit_curve(self, dataset, median_filter=True):
        return self.fit_func(dataset, median_filter)

    def eval_curve(self, xs):
        return self.eval_func(xs)


    def _fit_poly(self, dataset):
        '''
        Do a lsq fit of an (deg)th degree polynomial to the dataset data and return a
        numpy polynomial object 
        '''
        xs, ys, _ = dataset.data.T
        coefs = polyfit(xs, ys, self.deg)
        return coefs

    def _fit_poly_to_background(self, dataset, min_filter=True):
        dataset2 = dataset.copy()
        if min_filter:
            filter_length = dataset.data.shape[0]/self.deg/2
            dataset2.data[:,1] = \
                sn.filters.minimum_filter(dataset.data[:,1], size=filter_length, mode='nearest')
        self.coefs = self._fit_poly(dataset2)
        return self.coefs

    def _eval_poly_at_xs(self, xs):
        return polyval(xs, self.coefs)

    def _fit_spline_to_background(self, dataset, min_filter=True):
        dataset2 = dataset.copy()
        if min_filter:
            filter_length = dataset.data.shape[0]/self.deg/2
            dataset2.data[:,1] = \
                sn.filters.minimum_filter(dataset.data[:,1], size=filter_length, mode='nearest')
        factor = dataset2.data.shape[0]/10
        self.y_interpolator = interpolate.UnivariateSpline(dataset2.data[::factor,0], dataset2.data[::factor,1], s=0)
        return self.y_interpolator

    def _eval_spline_at_xs(self, xs):
        return self.y_interpolator(xs)

               
    def _background_test(self,xdata,order,params):
        background=np.zeros_like(xdata)
        for iback in range(order):
            background+=params[iback]*(xdata-xdata[0])**iback
        return background
    


if __name__=='__main__':
    import xye
    import matplotlib.pyplot as plt
    dataset = xye.XYEDataset.from_file(r'tests/testdata/si640c_low_temp_cal_p1_scan0.000000_adv0_0000.xye')
  # dataset = xye.XYEDataset.from_file(r'/home/jongl/Desktop/ht/si_al2o3_ht_p1_scan0.000000_adv0_0000.xye')

    deg = 7
    xs, ys, _ = dataset.data.T
    fitter = CurveFitter('Polynomial', deg)
    fitter.fit_curve(dataset)
    plt.plot(xs, fitter.eval_curve(xs))
    fitter = CurveFitter('Spline', deg)
    fitter.fit_curve(dataset)
    plt.plot(xs, fitter.eval_curve(xs))
    plt.plot(xs, ys, ',')
    plt.show()