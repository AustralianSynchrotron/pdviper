from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal

from .presenter import HeatmapDataPresenter


class HeatmapPanel(QWidget):
    def __init__(self, PlotWidgetCls):
        super().__init__()
        self._presenter = HeatmapDataPresenter()
        self._plot_widget = PlotWidgetCls(data_presenter=self._presenter)
        controls = HeatmapPlotControls(data_presenter=self._presenter)
        controls.zoom_reset.connect(self._plot_widget.reset_zoom)
        layout = QVBoxLayout()
        layout.addWidget(controls)
        layout.addWidget(self._plot_widget)
        self.setLayout(layout)

    def plot(self, data_sets):
        self._presenter.data_sets = data_sets
        self._plot_widget.plot()


class HeatmapPlotControls(QWidget):

    zoom_reset = pyqtSignal()

    def __init__(self, parent=None, *, data_presenter):
        super().__init__(parent)

        reset_zoom = QPushButton('Reset zoom')
        reset_zoom.clicked.connect(self.zoom_reset)

        layout = QHBoxLayout()
        layout.addWidget(reset_zoom)

        self.setLayout(layout)
