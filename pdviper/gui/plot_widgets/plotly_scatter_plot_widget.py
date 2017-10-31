import tempfile
import atexit
from pathlib import Path
import shutil
import os

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

from plotly import graph_objs as go
from plotly.offline import plot

from .xy_widget import XyPlotWidget, XyLegendState, verify_class_implements_abc


PLOT_TEMP_DIR = Path(tempfile.mkdtemp())


def _clean_temp_dir():
    shutil.rmtree(PLOT_TEMP_DIR)


atexit.register(_clean_temp_dir)


class PlotlyScatterPlotWidget(QWebEngineView):

    def __init__(self, parent=None):
        super().__init__(parent)
        profile = self.page().profile()
        profile.downloadRequested.connect(self._handle_download_request)
        self.data_sets = []
        self.legend = XyLegendState.OFF

    def plot(self):
        if len(self.data_sets) == 0:
            self.setHtml('')
            return
        traces = [go.Scatter(x=ds.angle, y=ds.intensity, name=ds.name)
                  for ds in self.data_sets]
        fig = go.Figure(data=traces, layout={'legend': {'x': .5, 'y': 1}})
        plot(fig, filename=str(self._plot_file_path), auto_open=False, show_link=False)
        self.load(QUrl(f'file://{self._plot_file_path}'))

    @property
    def _plot_file_path(self):
        try:
            path = self._cached_file_path
        except AttributeError:
            fd, path = tempfile.mkstemp(dir=PLOT_TEMP_DIR, suffix='.html')
            os.close(fd)
            path = Path(path)
            self._cached_file_path = path
        return path

    def _handle_download_request(self, download):
        download.accept()


verify_class_implements_abc(PlotlyScatterPlotWidget, XyPlotWidget)
