from os.path import basename
from numpy import loadtxt
import numpy as np

from parab import load_params


class XYEDataset(object):
    @staticmethod
    def _load_xye_data(filename):
        return loadtxt(filename)

    @staticmethod
    def from_file(filename, positions=2):
        data = XYEDataset._load_xye_data(filename)
        metadata = XYEDataset.load_metadata(filename)
        return XYEDataset(data, name=basename(filename), source=filename,
                          metadata=metadata)

    @staticmethod
    def load_metadata(filename):
        base_filename = filename.rsplit('.', 1)[0]
        parab_filename = base_filename + '.parab'
        try:
            params = load_params(parab_filename)
        except IOError:
            params = {}
        return params

    def __init__(self, data, name='', source='', metadata={}):
        self.name = name
        self.metadata = metadata
#        self.data = np.core.records.fromarrays(data[:, [0, 1]].T.astype(np.float64), 
#                                               names='x, y',
#                                               formats = 'f8, f8')
        self.x = data[:,0]
        self._y = data[:,1]
        self.source = source

    @property
    def y(self):
        # if the normalise checkbox is checked, normalise y when accessed here.

#        return self.data['y']
        return self._y
    @y.setter
    def y(self, value):
        self._y = value

    def add_param(self, name, value):
        self.metadata[name] = value