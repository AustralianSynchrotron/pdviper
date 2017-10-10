import pandas as pd


class DataManager:
    def __init__(self):
        self.data_sets = []
        self._callbacks = set()

    def load(self, paths):
        self.data_sets.extend(DataSet(p) for p in paths)
        self._process_callbacks()

    def add_callback(self, callback):
        self._callbacks.add(callback)

    def remove_callback(self, callback):
        self._callbacks.remove(callback)

    def _process_callbacks(self):
        for callback in self._callbacks:
            callback()


class DataSet:
    """A single data set of diffraction data.

    Attributes:
        angle (array[float]): Angle values in degrees
        intensity (array[float]): Intensity values
        intensity_stdev (array[float]): Standard deviation of intensity values
    """

    def __init__(self, path):
        self.source = path
        self._load_xye(path)

    def _load_xye(self, path):
        columns = ['angle', 'intensity', 'intensity_stdev']
        df = pd.read_csv(path, delimiter=' ', names=columns, index_col=False)
        self.angle = df.angle.values
        self.intensity = df.intensity.values
        self.intensity_stdev = df.intensity_stdev.values
