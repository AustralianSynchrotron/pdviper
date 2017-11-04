from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal

from .options import XyLegendState


class XyPlotPanel(QWidget):
    def __init__(self, parent, PlotWidgetCls):
        super().__init__(parent)
        self._plot_widget = PlotWidgetCls()
        controls = XyPlotControls()
        controls.legend_state_changed.connect(self._handle_legend_state_changed)
        controls.zoom_reset.connect(self._plot_widget.reset_zoom)
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
    zoom_reset = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        show_legend = QCheckBox('Show legend')
        show_legend.stateChanged.connect(self._handle_show_legend_change)
        reset_zoom = QPushButton('Reset zoom')
        reset_zoom.pressed.connect(self.zoom_reset)
        layout = QHBoxLayout()
        layout.addWidget(show_legend)
        layout.addWidget(reset_zoom)
        self.setLayout(layout)

    def _handle_show_legend_change(self, state):
        legend_state = XyLegendState.ON if state == Qt.Checked else XyLegendState.OFF
        self.legend_state_changed.emit(legend_state)
