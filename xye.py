from os.path import basename
from numpy import loadtxt

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
        self.data = data[:, [0, 1]] #, dtype=[('x', 'f4'), ('y', 'f4')])
        #self.x, self.y = transpose(data[:, [0, 1]])
        self.source = source

    def y(self):
        return self.data[:, 1]

    def x(self):
        return self.data[:, 0]

