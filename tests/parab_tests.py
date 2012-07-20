import unittest
import nose
import parab


class ParabTests(unittest.TestCase):
    def setUp(self):
        self.params = parab.load_params(r'tests/testdata/si640c_low_temp_cal_p1_scan0.000000_adv0_0000.parab')

    def load_params_test(self):
        self.assertEqual(self.params['Ion Chamber Raw Counts'], 35327)
        self.assertEqual(self.params['date'].strip(), 'Thu May 24 21:19:27 EST 2012')
        self.assertEqual(self.params['Integration Time(microseconds)'], 1.2016e+08)


if __name__ == '__main__':
    nose.main()
