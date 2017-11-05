import tempfile
import atexit
from pathlib import Path
import shutil
import os

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

from plotly import graph_objs as go
from plotly.offline import plot

from .abstract_widget import XyPlotWidget
from .options import XyLegendState
from ..utils import verify_class_implements_abc


PLOT_TEMP_DIR = Path(tempfile.mkdtemp())


def _clean_temp_dir():
    shutil.rmtree(PLOT_TEMP_DIR)


atexit.register(_clean_temp_dir)


class PlotlyScatterPlotWidget(QWebEngineView):

    def __init__(self, parent=None, *, data_presenter):
        super().__init__(parent)
        profile = self.page().profile()
        profile.downloadRequested.connect(self._handle_download_request)
        self._data_presenter = data_presenter
        self.legend = XyLegendState.OFF

    def plot(self):
        if len(self._data_presenter.series) == 0:
            self.setHtml('')
            return
        traces = [go.Scatter(x=s.x, y=s.y, name=s.name)
                  for s in self._data_presenter.series]
        if self.legend == XyLegendState.OFF:
            layout = go.Layout(showlegend=False)
        else:
            layout = go.Layout(legend={'x': .5, 'y': 1})
        fig = go.Figure(data=traces, layout=layout)
        plot(fig, filename=str(self._plot_file_path), auto_open=False, show_link=False)
        self.load(QUrl(f'file://{self._plot_file_path}'))

    def reset_zoom(self):
        self.plot()

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
