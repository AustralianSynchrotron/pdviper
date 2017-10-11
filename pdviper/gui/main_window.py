from PyQt5.QtWidgets import QWidget, QHBoxLayout, QSizePolicy

from .controls_panel import ControlsPanel
from .plot_window import PlotWindow


class MainWindow(QWidget):
    def __init__(self, *, data_manager):
        super().__init__()
        self.data_manager = data_manager
        self.setWindowTitle('PDViPeR')
        mainLayout = QHBoxLayout(self)

        self.controlsPanel = ControlsPanel(data_manager=self.data_manager)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        self.controlsPanel.setSizePolicy(sizePolicy)

        self.plotWindow = PlotWindow(data_manager=self.data_manager)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(1)
        self.plotWindow.setSizePolicy(sizePolicy)

        mainLayout.addWidget(self.controlsPanel)
        mainLayout.addWidget(self.plotWindow)
        self.setLayout(mainLayout)
        self.setGeometry(300, 300, 800, 600)
