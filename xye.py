import logger
from os.path import basename, split, splitext
from numpy import loadtxt, savetxt, asfarray
import numpy as np
from csv import reader
from pandas import read_csv

from parab import load_params
from copy import deepcopy
from data_formats import read_raw

class XYEDataset(object):
    @classmethod
    def _load_xye_data(cls, filename):
        try:
            return cls._load_xye_data_fast2(filename)
        except Exception as ex:
            print ex.message
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
    def _load_xye_data_fast2(filename, dtype=np.float64, skiprows=1, delimiter=' '):
        df = read_csv(filename,dtype=np.float64,delim_whitespace=True)
        a = df.get_values()
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

    @staticmethod
    def _load_bruker_raw_data(filename):
        data_array, meta_data = read_raw(filename)
        return data_array,meta_data



    @classmethod
    def from_file(cls, filename, positions=2):
        if splitext(filename)[1]=='.raw':
            data,metadata = cls._load_bruker_raw_data(filename)
        else:
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
   #     logger.logger.info('Saved {}'.format(filename))
        
    def save_fxye(self,filename):
        f=open(filename,'w')
        newx=self.data[:,0]*100
        newdata=np.column_stack((newx,self.data[:,1],self.data[:,2]))
        f.writelines(['Automatically generated file {} from PDViPeR \n'.format(splitext(basename(filename))[0]),
                     'BANK\t1\t{0}\t{1}\tCONS\t{2}\t{3} 0 0 FXYE \n'.format(len(newx),len(self.data[:,1]),newx[0],newx[1]-newx[0])])
        savetxt(filename, newdata, fmt='%1.6f')

    def copy(self):
        return deepcopy(self)

