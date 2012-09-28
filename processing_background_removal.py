import numpy as np
import scipy.ndimage as sn
from numpy.polynomial.polynomial import polyfit, polyval
from scipy import interpolate
import re


__doc__ = \
"""
Routines to remove background.
"""

def subtract_background_from_all_datasets(datasets, background, background_fit):
    processed_datasets = []
    for d in datasets:
        if background is not d and background_fit is not d:
            if background_fit is not None:
                dataset = subtract_background(d, background_fit)
            else:
                dataset = subtract_background(d, background)
            processed_datasets.append(dataset)
            dataset.name = re.sub('(_p[1-4]*)(_(?:n?s?m?g?)|_)_?',
                                   r'\1\2b_',
                                   dataset.name)
            dataset.metadata['ui'].name = dataset.name + ' (processed)'
            dataset.metadata['ui'].color = None
    return processed_datasets


def subtract_background(foreground, background):
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
    dataset.data = np.c_[xs, dataset.data[:,1] - y_interpolator(xs), dataset.data[:,2] + e_interpolator(xs)]
    return dataset


class CurveFitter:
    def __init__(self, curve_type, deg):
        self.fit_func = {'Spline' : self._fit_spline_to_background,
                         'Polynomial' : self._fit_poly_to_background}[curve_type]
        self.eval_func = {'Spline' : self._eval_spline_at_xs,
                          'Polynomial' : self._eval_poly_at_xs}[curve_type]
        self.deg = deg
        self.min_filter_length = 100 

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
        self.y_interpolator = interpolate.UnivariateSpline(dataset2.data[::factor,0], dataset2.data[::factor,1], s=3)
        return self.y_interpolator

    def _eval_spline_at_xs(self, xs):
        return self.y_interpolator(xs)


if __name__=='__main__':
    import xye
    import matplotlib.pyplot as plt
#    dataset = xye.XYEDataset.from_file(r'tests/testdata/si640c_low_temp_cal_p1_scan0.000000_adv0_0000.xye')
    dataset = xye.XYEDataset.from_file(r'../PD_example/Qinfen_data/4781/empty_p1_0000.xye')

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