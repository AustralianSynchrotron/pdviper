from pathlib import Path
from itertools import product

import pandas as pd
import numpy as np


class DataManager:
    def __init__(self):
        self.data_sets = []
        self._observers = set()

    def load(self, paths):
        paths = self._discard_paths_that_dont_exist(paths)
        paths = self._discard_paths_that_have_already_been_loaded(paths)
        if not paths:
            return
        start_index = len(self.data_sets)
        self.data_sets.extend(DataSet.from_xye(p) for p in paths)
        stop_index = len(self.data_sets)
        self._notify_observers('data_sets_added', list(range(start_index, stop_index)))

    def remove(self, indexes):
        sorted_indexes = list(sorted(indexes))
        for index in reversed(sorted_indexes):
            del self.data_sets[index]
        self._notify_observers('data_sets_removed', sorted_indexes)

    def load_partners(self):
        paths = [ds.partner_path for ds in self.data_sets
                 if ds.partner_path is not None]
        self.load(paths)

    def add_observer(self, observer):
        self._observers.add(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def _notify_observers(self, method_name, indices):
        for observer in self._observers:
            method = getattr(observer, method_name, None)
            if method:
                method(indices)

    def _discard_paths_that_dont_exist(self, paths):
        paths = (Path(p) for p in paths)
        return [p for p in paths if p.exists()]

    def _discard_paths_that_have_already_been_loaded(self, paths):
        loaded_paths = {ds.path for ds in self.data_sets if ds.path is not None}
        return [p for p in paths if p not in loaded_paths]


class DataSet:
    """A single data set of diffraction data.

    Attributes:
        name (str): Name of data set
        angle (array[float]): Angle values in degrees
        intensity (array[float]): Intensity values
        intensity_stdev (array[float]): Standard deviation of intensity values
        path (Path): Path to data set file

    """
    def __init__(self, name, angle, intensity, intensity_stdev, path=None):
        self.name = name
        self.angle = np.array(angle, 'float64')
        self.intensity = np.array(intensity, 'float64')
        self.intensity_stdev = np.array(intensity_stdev, 'float64')
        self.path = Path(path) if path is not None else None

    @classmethod
    def from_xye(cls, path):
        path = Path(path)
        name = path.stem
        columns = ['angle', 'intensity', 'intensity_stdev']
        df = pd.read_csv(path, delimiter=' ', names=columns, index_col=False)
        angle = df.angle.values
        intensity = df.intensity.values
        intensity_stdev = df.intensity_stdev.values
        return cls(name, angle, intensity, intensity_stdev, path)

    @property
    def partner_path(self):
        if self.path is None:
            return None
        mappings = {'1': '2', '3': '4', '12': '34'}
        mappings.update({target: src for src, target in mappings.items()})
        prefixes = ['p', 'P']
        filename = self.path.name
        for (source, target), prefix in product(mappings.items(), prefixes):
            search_str, repl_str = f'_{prefix}{source}_', f'_{prefix}{target}_'
            if search_str in filename:
                partner_filename = filename.replace(search_str, repl_str)
                break
        else:
            return None
        return self.path.with_name(partner_filename)
