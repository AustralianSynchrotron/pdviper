import unittest
import nose
import parab
import processing
import xye


class PeakDetectionTest(unittest.TestCase):
    def setUp(self):
        self.params = parab.load_params(r'tests/testdata/si640c_low_temp_cal_p1_scan0.000000_adv0_0000.parab')
        self.data = xye.XYEDataset.from_file(r'tests/testdata/si640c_low_temp_cal_p1_scan0.000000_adv0_0000.xye')

    def find_peak_test(self):
        # these magic indices are found by examining the si640c_low_temp_cal_p1_scan0.000000_adv0_0000.xye dataset
        data_x = self.data.x()[1686:1735]
        data_y = self.data.y()[1686:1735]
        peak_offset = processing.fit_peak_2theta(data_x, data_y, plot=False)
        LOW_2TH = 24.8278
        HIGH_2TH = 24.8280
        self.assertTrue(LOW_2TH < peak_offset < HIGH_2TH)

    def find_peaks_test(self):
        peak_offsets = processing.fit_peaks_2theta(self.data, plot=False)
        LOW_2TH = 24.8278
        HIGH_2TH = 24.8280
        self.assertTrue(LOW_2TH < peak_offsets[0] < HIGH_2TH)


if __name__ == '__main__':
    nose.main()
