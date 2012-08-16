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
        peak_offset, _ = processing.fit_peak_2theta(data_x, data_y, plot=False)
        LOW_2TH = 24.8278
        HIGH_2TH = 24.8280
        self.assertTrue(LOW_2TH < peak_offset < HIGH_2TH)


class MergeTest(unittest.TestCase):
    def setUp(self):
        pass

    def merge_constructed_data_test(self):
        x1data = np.r_[0:4, 3:6]
        x2data = np.r_[0:3, 2:6] + 0.5
        data1 = np.c_[x1data,x1data,x1data]
        data2 = np.c_[x2data,x2data,x2data]
        merged = processing.combine_by_merge(data1, data2)
        self.assertTrue(merged.shape==(12,3))

    def splice_constructed_data_test(self):
        x1data = np.r_[0:2, 4:6, 7:9]
        x2data = np.arange(6) + 0.5
        data1 = np.c_[x1data,x1data,x1data]
        data2 = np.c_[x2data,x2data,x2data]
        merged = processing.combine_by_splice(data1, data2, gap_threshold=1.5)
        self.assertTrue(np.allclose(merged[:,0],
                             np.r_[0., 1., 1.5, 2.5, 3.5, 4., 5., 5.5, 7., 8.]))
        self.assertTrue(np.allclose(merged[:,1],
                             np.r_[0., 1., 1.5, 2.5, 3.5, 4., 5., 5.5, 7., 8.]))
        self.assertTrue(np.allclose(merged[:,2],
                             np.r_[0., 1., 1.5, 2.5, 3.5, 4., 5., 5.5, 7., 8.]))

    def clean_gaps_test(self):
        data = np.arange(13)
        data = np.delete(data, [3,9])
        data = np.c_[data,data,data]
        data = processing.clean_gaps(data, gap_threshold=1.5, shave_number=2)
        self.assertTrue(np.alltrue(data[:,0]==np.r_[0,6,12]))

    def regrid_data_test(self):
        # test that regridding preserves the y-data if resampled at the x-data points
        np.random.seed(42)
        POINTS = 50000
        data = np.c_[np.arange(POINTS), np.random.rand(POINTS), np.arange(POINTS)]
        newdata = processing.regrid_data(data, interval=1.0)
        self.assertTrue(np.allclose(data, newdata))

    def regrid_data_test2(self):
        # test that regridding preserves the y-data if resampled near the x-data points
        np.random.seed(42)
        POINTS = 5
        data = np.c_[np.arange(POINTS), np.random.rand(POINTS), np.arange(POINTS)]
        newdata = processing.regrid_data(data, start=0.000001, end=data[:,0][-1]+.000001, interval=1.0)
        self.assertTrue(np.allclose(data, newdata, atol=1e-4))


class NormalisationTest(unittest.TestCase):
    def setUp(self):
        pass

    def normalise_data_test(self):
        # test that normalisation leaves the x-data untouched and rescales the y and e correctly
        DETECTOR_COUNTS = 3.0
        COUNT_KEY = 'Integrated Ion Chamber Count(counts)'
        data1 = np.c_[[0.,1,2,3], [0,10,20,30], [0,1,2,3]]
        data2 = np.c_[[1.,2,3,4], [0,5,10,20], [0,1,2,3]]
        dataset1 = xye.XYEDataset(data1, metadata={COUNT_KEY:1.0})
        dataset2 = xye.XYEDataset(data2, metadata={COUNT_KEY:1.0/DETECTOR_COUNTS})
        dataset_pair = (dataset1, dataset2)
        result = processing.normalise_dataset(dataset_pair)
        self.assertTrue(np.allclose(result[:,0], data2[:,0]))                # check x's
        self.assertTrue(np.allclose(result[:,1], data2[:,1]*DETECTOR_COUNTS)) # check y's
        self.assertTrue(np.allclose(result[:,2], data2[:,2]*np.sqrt(DETECTOR_COUNTS))) # check e's

if __name__ == '__main__':
    nose.main()
