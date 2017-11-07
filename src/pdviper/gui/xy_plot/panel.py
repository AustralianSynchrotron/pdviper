from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton,
                             QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
import numpy as np

from .options import XyLegendState
from .presenter import XyDataPresenter, AxisScaler


class XyPlotPanel(QWidget):
    def __init__(self, parent, PlotWidgetCls):
        super().__init__(parent)
        self._presenter = XyDataPresenter(
            x_scales=[
                AxisScaler('Normal', axis_label='Angle (2θ)'),
            ],
            y_scales=[
                AxisScaler('Linear', axis_label='Intensity (N)'),
                AxisScaler('Log', axis_label='Intensity (log₁₀(N))',
                           transformation=lambda x: np.log10(x)),
                AxisScaler('Sqrt', axis_label='Intensity (√N)',
                           transformation=lambda x: np.sqrt(x)),
            ],
        )
        self._plot_widget = PlotWidgetCls(data_presenter=self._presenter)
        controls = XyPlotControls(data_presenter=self._presenter)
        controls.legend_state_changed.connect(self._handle_legend_state_changed)
        controls.y_transform_changed.connect(self._y_transform_changed)
        controls.zoom_reset.connect(self._plot_widget.reset_zoom)
        layout = QVBoxLayout()
        layout.addWidget(controls)
        layout.addWidget(self._plot_widget)
        self.setLayout(layout)

    def plot(self, data_sets):
        self._presenter.data_sets = data_sets
        self._plot_widget.plot()

    def _handle_legend_state_changed(self, state):
        self._plot_widget.legend = state
        self._plot_widget.plot()

    def _y_transform_changed(self, name):
        self._presenter.set_y_scale(name)
        self._plot_widget.plot(preserve_zoom=False)


class XyPlotControls(QWidget):

    legend_state_changed = pyqtSignal(XyLegendState)
    y_transform_changed = pyqtSignal(str)
    zoom_reset = pyqtSignal()

    def __init__(self, parent=None, *, data_presenter):
        super().__init__(parent)

        show_legend = QCheckBox('Show legend')
        show_legend.stateChanged.connect(self._handle_show_legend_change)

        y_transforms = QComboBox()
        for name in data_presenter.y_scale_options:
            y_transforms.addItem(name)
        y_transforms.currentTextChanged.connect(self.y_transform_changed)

        reset_zoom = QPushButton('Reset zoom')
        reset_zoom.clicked.connect(self.zoom_reset)

        layout = QHBoxLayout()
        layout.addWidget(show_legend)
        layout.addWidget(y_transforms)
        layout.addWidget(reset_zoom)

        self.setLayout(layout)

    def _handle_show_legend_change(self, state):
        legend_state = XyLegendState.ON if state == Qt.Checked else XyLegendState.OFF
        self.legend_state_changed.emit(legend_state)