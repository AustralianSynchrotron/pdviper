from PyQt5.QtWidgets import QWidget, QHBoxLayout

from .controls_panel import ControlsPanel
from .plot_window import PlotWindow


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PDViPeR')
        mainLayout = QHBoxLayout(self)
        mainLayout.addWidget(ControlsPanel())
        mainLayout.addWidget(PlotWindow())
        self.setLayout(mainLayout)
        self.setGeometry(300, 300, 800, 600)
