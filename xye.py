from os.path import basename
from numpy import loadtxt, savetxt, asfarray
from csv import reader

from parab import load_params
from copy import deepcopy


class XYEDataset(object):
    @classmethod
    def _load_xye_data(cls, filename):
        try:
            return cls._load_xye_data_fast(filename)
        except:
            return cls._load_xye_data_slow(filename)

    @staticmethod
    def _load_xye_data_fast(filename):
        row_reader = reader(open(filename), delimiter=' ', skipinitialspace=True)
        return asfarray([ row[:3] for row in row_reader ])

    @staticmethod
    def _load_xye_data_slow(filename):
        return loadtxt(filename)

    @classmethod
    def from_file(cls, filename, positions=2):
        data = cls._load_xye_data(filename)
        metadata = cls.load_metadata(filename)
        return cls(data, name=basename(filename), source=filename,
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
        self.data = data[:, :3]
        self.source = source

    def x(self):
        return self.data[:, 0]

    def y(self):
        return self.data[:, 1]

    def e(self):
        return self.data[:, 2]

    def add_param(self, name, value):
        self.metadata[name] = value

    def save(self, filename):
        savetxt(filename, self.data, fmt='%1.6f')

    def copy(self):
        return deepcopy(self)

