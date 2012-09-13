import unittest
import numpy as np
import nose
import processing_rescale
import wavelength_editor
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
        processing_rescale.rescale_xye_datasets(self.data_plus_scale_sets, 1.0, 'd', 'd')
        self.assertTrue(np.allclose(self.data_plus_scale_sets[0].dataset.x(), [2.,3,4,5]))
        self.assertTrue(np.allclose(self.data_plus_scale_sets[1].dataset.x(), [1.,2,3,4]))

    def twotheta_to_d_test(self):
        processing_rescale.rescale_xye_datasets(self.data_plus_scale_sets, 1.0, 'theta', 'd')
        self.assertTrue(np.allclose(self.data_plus_scale_sets[0].dataset.x(),
                                    [42.97401637, 28.65116251, 21.49028126, 17.19418922]))
        self.assertTrue(np.allclose(self.data_plus_scale_sets[1].dataset.x(),
                                    [28.64825337, 14.32467212, 9.5503875, 7.16342709]))

    def twotheta_to_Q_test(self):
        processing_rescale.rescale_xye_datasets(self.data_plus_scale_sets, 1.0, 'theta', 'Q')
        self.assertTrue(np.allclose(self.data_plus_scale_sets[0].dataset.x(),
                                    [0.14620894, 0.21929949, 0.29237334, 0.36542493]))
        self.assertTrue(np.allclose(self.data_plus_scale_sets[1].dataset.x(),
                                    [0.21932176, 0.43862681, 0.65789847, 0.87712002]))

    def d_to_Q_test(self):
        processing_rescale.rescale_xye_datasets(self.data_plus_scale_sets, 1.0, 'd', 'Q')
        self.assertTrue(np.allclose(self.data_plus_scale_sets[0].dataset.x(),
                                    [3.14159265, 2.0943951, 1.57079633, 1.25663706]))
        self.assertTrue(np.allclose(self.data_plus_scale_sets[1].dataset.x(),
                                    [6.28318531, 3.14159265, 2.0943951, 1.57079633]))

    def twotheta_to_twotheta_test(self):
        processing_rescale.rescale_xye_datasets(self.data_plus_scale_sets, 15.0, 'theta', 'theta')
        self.assertTrue(np.allclose(self.data_plus_scale_sets[0].dataset.x(),
                                    [20.10192559, 30.3501659, 40.85171026, 51.72257254]))
        self.assertTrue(np.allclose(self.data_plus_scale_sets[1].dataset.x(),
                                    [30.35332202, 63.14434728, 103.4984301]))

if __name__ == '__main__':
    nose.main()
