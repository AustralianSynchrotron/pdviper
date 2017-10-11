from PyQt5.QtWidgets import QWidget, QVBoxLayout

from .plot_widgets.qtcharts_xy_widget import QtChartsXyPlotWidget


class PlotWindow(QWidget):
    def __init__(self, parent=None, *, data_manager):
        super().__init__(parent)
        self._plotWidget = QtChartsXyPlotWidget()
        layout = QVBoxLayout()
        layout.addWidget(self._plotWidget)
        self.setLayout(layout)
        self._data_manager = data_manager
        data_manager.add_callback(self.handleDataManagerUpdate)

    def handleDataManagerUpdate(self):
        self.plot()

    def plot(self):
        self._plotWidget.plot(self._data_manager.data_sets)
