from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QTableView
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QFont
from PyQt5.QtCore import Qt, pyqtSignal

from .controls_panel import ControlsPanel
from .plot_window import PlotWindow


class DataModel(QStandardItemModel):

    changed = pyqtSignal()

    def __init__(self, data_manager, parent):
        super().__init__(0, 2, parent)
        self.data_manager = data_manager
        self.data_manager.add_observer(self)
        self.setHeaderData(0, Qt.Horizontal, 'Name')
        self.setHeaderData(1, Qt.Horizontal, 'Colour')
        self._updating = False
        self.itemChanged.connect(self.handleItemChanged)

    def data_sets_added(self, indices):
        self._updating = True
        for row in indices:
            ds = self.data_manager.data_sets[row]
            item = QStandardItem(ds.name)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            font = QFont()
            font.setPointSize(10)
            item.setFont(font)
            self.setItem(row, 0, item)
        self._updating = False
        self.changed.emit()

    def handleItemChanged(self, item):
        if not self._updating:
            self.changed.emit()

    def get_active_datasets(self):
        data_sets = []
        for row in range(self.rowCount()):
            if self.item(row, 0).checkState() == Qt.Unchecked:
                continue
            data_sets.append(self.data_manager.data_sets[row])
        return data_sets


class MainWindow(QWidget):
    def __init__(self, *, data_manager):
        super().__init__()

        self.setWindowTitle('PDViPeR')
        self.dataSetsModel = model = DataModel(data_manager, self)

        self.controlsPanel = ControlsPanel(data_manager=data_manager)
        self.dataSetsTable = QTableView()
        self.plotWindow = PlotWindow(model=model)

        self.dataSetsTable.setModel(self.dataSetsModel)
        self.dataSetsTable.setColumnWidth(0, 220)
        self.dataSetsTable.setColumnWidth(1, 50)

        lhsLayout = QVBoxLayout()
        lhsLayout.addWidget(self.controlsPanel)
        lhsLayout.addWidget(self.dataSetsTable)
        lhsWidget = QWidget()
        lhsWidget.setLayout(lhsLayout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(lhsWidget)
        splitter.addWidget(self.plotWindow)

        mainLayout = QHBoxLayout(self)
        mainLayout.addWidget(splitter)
        self.setLayout(mainLayout)

        self.setGeometry(300, 300, 1200, 800)
        splitter.setSizes([300, 800])
