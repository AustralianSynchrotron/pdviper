from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal

from .plot_widgets.qtcharts_xy_widget import QtChartsXyPlotWidget
from .plot_widgets.plotly_scatter_plot_widget import PlotlyScatterPlotWidget
from .plot_widgets.xy_widget import XyLegendState


class PlotWindow(QWidget):
    def __init__(self, parent=None, *, model):
        super().__init__(parent)
        self._active_plot = self._xy_plot = XyPlotPanel(self, QtChartsXyPlotWidget)
        self._3d_plot = XyPlotPanel(self, PlotlyScatterPlotWidget)
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


class XyPlotPanel(QWidget):
    def __init__(self, parent, PlotWidgetCls):
        super().__init__(parent)
        self._plot_widget = PlotWidgetCls()
        controls = XyPlotControls()
        controls.legend_state_changed.connect(self._handle_legend_state_changed)
        layout = QVBoxLayout()
        layout.addWidget(controls)
        layout.addWidget(self._plot_widget)
        self.setLayout(layout)

    def plot(self, data_sets):
        self._plot_widget.data_sets = data_sets
        self._plot_widget.plot()

    def _handle_legend_state_changed(self, state):
        self._plot_widget.legend = state
        self._plot_widget.plot()


class XyPlotControls(QWidget):

    legend_state_changed = pyqtSignal(XyLegendState)

    def __init__(self, parent=None):
        super().__init__(parent)
        show_legend = QCheckBox('Show legend')
        show_legend.stateChanged.connect(self._handle_show_legend_change)
        layout = QVBoxLayout()
        layout.addWidget(show_legend)
        self.setLayout(layout)

    def _handle_show_legend_change(self, state):
        legend_state = XyLegendState.ON if state == Qt.Checked else XyLegendState.OFF
        self.legend_state_changed.emit(legend_state)
