import unittest
import nose
import parab
import processing
import xye


class PeakDetectionTest(unittest.TestCase):
    def setUp(self):
        self.params = parab.load_params(r'tests/testdata/si640c_low_temp_cal_p1_scan0.000000_adv0_0000.parab')
        self.data = xye.XYEDataset.from_file(r'tests/testdata/si640c_low_temp_cal_p1_scan0.000000_adv0_0000.xye')

    def find_highest_peak_test(self):
        peak_offset = processing.highest_peak_2theta(self.data)
        LOW_2TH = 24.83063
        HIGH_2TH = 24.83065
        self.assertTrue(LOW_2TH < peak_offset < HIGH_2TH)


if __name__ == '__main__':
    nose.main()
