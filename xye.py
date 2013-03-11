import logger
from os.path import basename, split
from numpy import loadtxt, savetxt, asfarray
import numpy as np
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
        a = asfarray([ row[:3] for row in row_reader ])
        if a.shape[1] == 2:
            # only 2-columns of data in input, so identify this as xy data
            # and append a column of zeros.
            a = np.hstack((a, np.zeros((a.shape[0],1))))
        return a

    @staticmethod
    def _load_xye_data_slow(filename):
        a = loadtxt(filename)
        if a.shape[1] == 2:
            # only 2-columns of data in input, so identify this as xy data
            # and append a column of zeros.
            a = np.hstack((a, np.zeros((a.shape[0],1))))
        return a

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
        open(filename,'w')
        savetxt(filename, self.data, fmt='%1.6f')
        logger.logger.info('Saved {}'.format(filename))
        

    def copy(self):
        return deepcopy(self)

