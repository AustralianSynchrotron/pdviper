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
        self._notify_observers('data_sets_added', list(range(start_index, stop_index)))

    def remove(self, indexes):
        sorted_indexes = list(sorted(indexes))
        for index in reversed(sorted_indexes):
            del self.data_sets[index]
        self._notify_observers('data_sets_removed', sorted_indexes)

    def add_observer(self, observer):
        self._observers.add(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def _notify_observers(self, method_name, indices):
        for observer in self._observers:
            method = getattr(observer, method_name, None)
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
