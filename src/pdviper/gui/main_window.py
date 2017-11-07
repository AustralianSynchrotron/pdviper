from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from .controls_panel import ControlsPanel
from .visualisation_panel import VisualisationPanel
from .data_sets_table import DataSetsTable, DataSetsModel


class MainWindow(QWidget):
    def __init__(self, *, data_manager):
        super().__init__()

        self.setWindowTitle('PDViPeR')
        self._data_sets_model = model = DataSetsModel(data_manager, self)

        self._controls_panel = ControlsPanel(data_manager=data_manager)
        self._data_sets_table = DataSetsTable(model=model)
        self._visualisation_panel = VisualisationPanel(model=model)

        lhs_layout = QVBoxLayout()
        lhs_layout.addWidget(self._controls_panel)
        lhs_layout.addWidget(self._data_sets_table)
        lhs_widget = QWidget()

        lhs_widget.setLayout(lhs_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(lhs_widget)
        splitter.addWidget(self._visualisation_panel)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

        self.setGeometry(300, 300, 1200, 800)
        splitter.setSizes([450, 650])
