import unittest
import nose
import parab
import processing
import xye
import numpy as np
from numpy import r_


class XyeTest(unittest.TestCase):
    def setUp(self):
        self.params = parab.load_params(r'tests/testdata/si640c_low_temp_cal_p1_scan0.000000_adv0_0000.parab')
        self.data = xye.XYEDataset.from_file(r'tests/testdata/si640c_low_temp_cal_p1_scan0.000000_adv0_0000.xye')

    def read_x_test(self):
        self.assertTrue(self.data.x.shape == (20458L,))
        self.assertTrue(np.allclose(self.data.x[0], 18.182600))
        self.assertTrue(np.allclose(self.data.x[-1], 98.003922))

    def write_x_test(self):
        self.data.x[0] = self.data.x[-1] = 42.0
        self.assertTrue(np.allclose(self.data.x[:2], r_[42.0, 18.186354]))
        self.assertTrue(np.allclose(self.data.x[-2:], r_[98.000168, 42.0]))

    def read_y_test(self):
        self.assertTrue(self.data.y.shape == (20458L,))
        self.assertTrue(np.allclose(self.data.y[0], 1767.909668))
        self.assertTrue(np.allclose(self.data.y[-1], 436.572968))

    def write_y_test(self):
        self.data.y[0] = self.data.y[-1] = 42.0
        self.assertTrue(np.allclose(self.data.y[:2], r_[42.0, 1724.592163]))
        self.assertTrue(np.allclose(self.data.y[-2:], r_[474.036743, 42.0]))

if __name__ == '__main__':
    nose.main()
