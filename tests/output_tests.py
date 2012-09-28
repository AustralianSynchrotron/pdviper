import os
import unittest
import nose
import xye
from nose import SkipTest
#from nose.tools import ok_

from raw_data_plot import RawDataPlot
from chaco_output import PlotOutput

from chaco.api import OverlayPlotContainer

class OutputTest(unittest.TestCase):
    def setUp(self):
        if 'OUTPUT_TESTS' not in os.environ:
            raise SkipTest('Slow: define OUTPUT_TESTS to run')
        self.data = xye.XYEDataset.from_file(r'tests/testdata/si640c_low_temp_cal_p1_scan0.000000_adv0_0000.xye')
        class UI(object):
            color = None
            name = ''
            active = True
            markers = False
        self.data.metadata['ui'] = UI()
        self.datasets = [ self.data ]
        self.plot = RawDataPlot(self.datasets)
        self.plot.plot_datasets(self.datasets, scale='log')
        self.container = OverlayPlotContainer(self.plot.get_plot(),
            bgcolor="white", use_backbuffer=True,
            border_visible=False)
        self.container.request_redraw()
        self.basedir = os.path.join('tests', 'tmp')
        try:
            os.mkdir(self.basedir)
        except OSError, e:
            assert 'exists' in str(e)

    def _save_plot(self, filename):
        PlotOutput.save_as_image(self.container, self.basedir + filename, width=800, height=600)

    def test_png_output(self):
        self._save_plot('test.png')

    def test_pdf_output(self):
        self._save_plot('test.pdf')

    def test_svg_output(self):
        self._save_plot('test.svg')

    def test_eps_output(self):
        self._save_plot('test.eps')



if __name__ == '__main__':
    nose.main()
