import unittest
import nose
import parab
import processing
import xye
import numpy as np


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


class MergeTest(unittest.TestCase):
    def setUp(self):
        testpath = r'tests/testdata/'
        prefix = 'BZA-scan_'

#        self.p1_0_params = parab.load_params(testpath + prefix + 'p1_0000.parab')
#        self.p1_1_params = parab.load_params(testpath + prefix + 'p1_0001.parab')
#        self.p2_0_params = parab.load_params(testpath + prefix + 'p2_0000.parab')
#        self.p2_1_params = parab.load_params(testpath + prefix + 'p2_0001.parab')

        self.p1_0_data = xye.XYEDataset.from_file(testpath + prefix + 'p1_0000.xye')
        self.p1_1_data = xye.XYEDataset.from_file(testpath + prefix + 'p1_0001.xye')
        self.p2_0_data = xye.XYEDataset.from_file(testpath + prefix + 'p2_0000.xye')
        self.p2_1_data = xye.XYEDataset.from_file(testpath + prefix + 'p2_0001.xye')

    def merge_constructed_data_test(self):
        x1data = np.hstack((np.arange(4),np.arange(3,6)))
        x2data = np.hstack((np.arange(3),np.arange(2,6)))+0.5
        data1 = xye.XYEDataset(data=np.vstack((x1data,x1data)).T)
        data2 = xye.XYEDataset(data=np.vstack((x2data,x2data)).T)
        merged = processing.combine_by_merge(data1, data2)
        self.assertTrue(merged.shape==(12,2))

#    def merge_test(self):
#        print processing.combine_by_merge(self.p1_0_data, self.p2_0_data)
#        print processing.combine_by_merge(self.p1_1_data, self.p2_1_data)
#        self.assertTrue(False)

if __name__ == '__main__':
    nose.main()
