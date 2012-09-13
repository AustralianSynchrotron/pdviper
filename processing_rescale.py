import numpy as np
from numpy import sin, arcsin, pi
import re
import os


__doc__ = \
"""
Routines to convert x/abscissa values in .xye data series between units theta, d and Q
which are related by Bragg's law.

\lambda = 2 d sin \theta 
and Q = 2*pi/d

The \lambda value for each .xye dataset may be different. It is entered by the user in the
table/spreadsheet view defined in wavelength_editor along with the desired conversion
type and target wavelength used for scaling.
"""

'''
The following dictionary-of-dictionaries is a function lookup table of unit-to-unit
conversion functions arranged with outer key equal to the source unit and inner key
equal to the destination unit.
'''
TWOPI = 2*pi
DEG_TO_RAD = pi/180
RAD_TO_DEG = 180/pi
conversion_functions = {
    'theta': {
        'theta':    lambda twotheta, lam1, lam2: 2.0*RAD_TO_DEG*arcsin(sin(twotheta*0.5*DEG_TO_RAD)*lam2/lam1),
        'd':        lambda twotheta, lam, _: lam/(2.0*sin(0.5*twotheta*DEG_TO_RAD)),
        'Q':        lambda twotheta, lam, _: 2.0*sin(0.5*twotheta*DEG_TO_RAD)/(lam/TWOPI),
        },
    'd': {
        'theta':    lambda d, lam, _: 2.0*RAD_TO_DEG*arcsin(lam/(2.0*d)),
        'd':        lambda x, _, _2: x,
        'Q':        lambda d, lam, _: TWOPI/d,
        },
    'Q': {
        'theta':    lambda Q, lam, _: 2.0*RAD_TO_DEG*arcsin(Q*(lam/TWOPI)/2.0),
        'd':        lambda Q, lam, _: TWOPI/Q,
        'Q':        lambda x, _, _2: x,
        },
    }


def rescale_xye_datasets(data_plus_scale_sets, target_value, convert_from, convert_to):
    '''
    This function takes as argument a list of WavelengthUI objects. Each WavelengthUI
    object contains a dataset and a wavelength scaling factor, used in evaluating the
    Bragg law during conversion to the new unit
    '''
    # When rescaling, 2theta might exceed 180deg, i.e. x>1 in arcsin(x), producing nan's
    # We allow this but suppress warnings, then cleanup afterwards.
    current_errorlevel = np.seterr(invalid='ignore')
    for data_plus_scale in data_plus_scale_sets:
        # find and call the conversion function
        f = conversion_functions[convert_from][convert_to]
        xs = f(data_plus_scale.dataset.data[:,0], data_plus_scale.x, target_value)
        # truncate data below 180deg 
        mask = ~np.isnan(xs)
        data_plus_scale.dataset.data = data_plus_scale.dataset.data[mask,:] 
        data_plus_scale.dataset.data[:,0] = xs[mask]
    np.seterr(invalid=current_errorlevel['invalid'])


def write_xye_datasets(data_plus_scale_sets, label):
    '''
    Writes the dataset to the same directory as the input file, including the label string
    immediately before the last group of index digits
    '''
    for d in data_plus_scale_sets:
        path, basename = os.path.split(d.dataset.source)
        filename = '{1}_{label}_{2}'.format(*re.split(r'(.+)_(\d+\..+)',
                                            basename), label=label)
        filename = os.path.join(path, filename)
        d.dataset.save(filename)
