from pathlib import Path

import pandas as pd
import numpy as np


class DataManager:
    def __init__(self):
        self.data_sets = []
        self._observers = set()

    def load(self, paths):
        start_index = len(self.data_sets)
        self.data_sets.extend(DataSet.from_xye(p) for p in paths)
        stop_index = len(self.data_sets)
        self._notify_data_sets_added(list(range(start_index, stop_index)))

    def add_observer(self, observer):
        self._observers.add(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def _notify_data_sets_added(self, indices):
        for observer in self._observers:
            method = getattr(observer, 'data_sets_added', None)
            if method:
                method(indices)


class DataSet:
    """A single data set of diffraction data.

    Attributes:
        angle (array[float]): Angle values in degrees
        intensity (array[float]): Intensity values
        intensity_stdev (array[float]): Standard deviation of intensity values
    """

    def __init__(self, name, angle, intensity, intensity_stdev):
        self.name = name
        self.angle = np.array(angle, 'float64')
        self.intensity = np.array(intensity, 'float64')
        self.intensity_stdev = np.array(intensity_stdev, 'float64')

    @classmethod
    def from_xye(cls, path):
        name = Path(path).stem

        columns = ['angle', 'intensity', 'intensity_stdev']
        df = pd.read_csv(path, delimiter=' ', names=columns, index_col=False)
        angle = df.angle.values
        intensity = df.intensity.values
        intensity_stdev = df.intensity_stdev.values

        return cls(name, angle, intensity, intensity_stdev)
