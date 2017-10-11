from PyQt5.QtWidgets import QWidget, QVBoxLayout

from .plot_widgets.plotly_scatter_plot_widget import (
    PlotlyScatterPlotWidget
)


class PlotWindow(QWidget):
    def __init__(self, parent=None, *, data_manager):
        super().__init__(parent)
        self._plotWidget = PlotlyScatterPlotWidget()
        layout = QVBoxLayout()
        layout.addWidget(self._plotWidget)
        self.setLayout(layout)
        self._data_manager = data_manager
        data_manager.add_callback(self.handleDataManagerUpdate)

    def handleDataManagerUpdate(self):
        self.plot()

    def plot(self):
        self._plotWidget.plot(self._data_manager.data_sets)
