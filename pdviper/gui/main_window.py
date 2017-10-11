from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from .controls_panel import ControlsPanel
from .plot_window import PlotWindow


class MainWindow(QWidget):
    def __init__(self, *, data_manager):
        super().__init__()
        self.data_manager = data_manager

        self.setWindowTitle('PDViPeR')

        self.controlsPanel = ControlsPanel(data_manager=self.data_manager)
        self.plotWindow = PlotWindow(data_manager=self.data_manager)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.controlsPanel)
        splitter.addWidget(self.plotWindow)

        mainLayout = QHBoxLayout(self)
        mainLayout.addWidget(splitter)
        self.setLayout(mainLayout)

        self.setGeometry(300, 300, 800, 600)
        splitter.setSizes([350, 350])
