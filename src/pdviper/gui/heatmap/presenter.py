from ...data_manager import DataSet

import numpy as np


class HeatmapDataPresenter:

    def __init__(self, *, x_step_size=0.00375):
        self.data_sets = []
        self._x_step_size = x_step_size

    @property
    def x_axis_label(self):
        return 'Angle'

    @property
    def y_axis_label(self):
        return 'Dataset'

    @property
    def z_axis_label(self):
        return 'Intensity'

    @property
    def data(self):
        if self.data_sets:
            data_sets = standardize_angles(self.data_sets, step=self._x_step_size)
            return np.vstack([ds.intensity for ds in data_sets])
        else:
            return np.zeros(shape=(0, 0))


def standardize_angles(data_sets, *, step):
    new_data_sets = []
    largest_start = max(ds.angle[0] for ds in data_sets)
    smallest_end = min(ds.angle[-1] for ds in data_sets)
    for ds in data_sets:
        new_ds = regrid(ds, step=step, start=largest_start, end=smallest_end)
        new_data_sets.append(new_ds)
    return new_data_sets


def regrid(data_set, *, step, start, end):
    data = data_set.data
    y_interpolator = lambda xs: np.interp(xs, data[:, 0], data[:, 1])  # noqa
    e_interpolator = lambda xs: np.interp(xs, data[:, 0], data[:, 2])  # noqa
    # we add a little bit to step to ensure the range is inclusive
    xs = np.arange(start, end + step / 2, step)
    new_data = np.c_[xs, y_interpolator(xs), e_interpolator(xs)]
    return DataSet(name=data_set.name,
                   angle=new_data[:, 0],
                   intensity=new_data[:, 1],
                   intensity_stdev=new_data[:, 2])
