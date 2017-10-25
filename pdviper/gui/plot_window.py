from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from .plot_widgets.qtcharts_xy_widget import QtChartsXyPlotWidget
from .plot_widgets.plotly_scatter_plot_widget import PlotlyScatterPlotWidget


class PlotWindow(QWidget):
    def __init__(self, parent=None, *, model):
        super().__init__(parent)
        self._active_plot = self._xy_plot = QtChartsXyPlotWidget()
        self._3d_plot = PlotlyScatterPlotWidget()
        layout = QVBoxLayout()
        self._tabs = tabs = QTabWidget(self)
        tabs.addTab(self._xy_plot, 'XY')
        tabs.addTab(self._3d_plot, '3D')
        layout.addWidget(tabs)
        self.setLayout(layout)
        self._model = model
        self._model.changed.connect(self._handle_data_model_change)
        tabs.currentChanged.connect(self._handle_tab_change)

    def _handle_data_model_change(self):
        self._plot()

    def _handle_tab_change(self, index):
        self._active_plot = self._tabs.currentWidget()
        self._plot()

    def _plot(self):
        self._active_plot.plot(self._model.get_active_datasets())
