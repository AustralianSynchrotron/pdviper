from PyQt5.QtWidgets import QWidget, QVBoxLayout

from .plot_widgets.qtcharts_xy_widget import QtChartsXyPlotWidget


class PlotWindow(QWidget):
    def __init__(self, parent=None, *, model):
        super().__init__(parent)
        self._plotWidget = QtChartsXyPlotWidget()
        layout = QVBoxLayout()
        layout.addWidget(self._plotWidget)
        self.setLayout(layout)
        self.model = model
        self.model.changed.connect(self.handleDataManagerUpdate)

    def handleDataManagerUpdate(self):
        self.plot()

    def plot(self):
        self._plotWidget.plot(self.model.get_active_datasets())
