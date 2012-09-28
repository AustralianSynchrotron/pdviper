import unittest
import numpy as np
import nose
from nose import SkipTest
import processing_background_removal
import xye
from traits.api import Enum, Float, Instance, HasTraits

class DatasetWithWavelength(HasTraits):
    dataset = Instance(object)
    x = Float

class RescaleTests(unittest.TestCase):
    def setUp(self):
        data1 = np.c_[[2.,3,4,5], [0,10,20,30], [0,1,2,3]]
        data2 = np.c_[[1.,2,3,4], [0,5,10,20], [0,1,2,3]]
        dataset1 = xye.XYEDataset(data1)
        dataset2 = xye.XYEDataset(data2)
        we1 = DatasetWithWavelength(dataset=dataset1, x=1.5)
        we2 = DatasetWithWavelength(dataset=dataset2, x=0.5)
        self.data_plus_scale_sets = [we1, we2]

    def no_rescale_test(self):
        #~ processing_rescale.rescale_xye_datasets(self.data_plus_scale_sets, 1.0, 'd', 'd')
        raise SkipTest
        self.assertTrue(True)

if __name__ == '__main__':
    nose.main()
