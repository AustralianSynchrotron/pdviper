from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QSplitter, QTableView
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, pyqtSignal

from .controls_panel import ControlsPanel
from .plot_window import PlotWindow


class DataModel(QStandardItemModel):

    changed = pyqtSignal()

    def __init__(self, data_manager, parent):
        super().__init__(0, 1, parent)
        self._data_manager = data_manager
        data_manager.add_observer(self)
        self.setHeaderData(0, Qt.Horizontal, 'Name')
        self._updating = False
        self.itemChanged.connect(self._handle_item_changed)

    def data_sets_added(self, indices):
        self._updating = True
        for row in indices:
            ds = self._data_manager.data_sets[row]
            item = QStandardItem(ds.name)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self.setItem(row, 0, item)
        self._updating = False
        self.changed.emit()

    def _handle_item_changed(self, item):
        if not self._updating:
            self.changed.emit()

    def get_active_datasets(self):
        data_sets = []
        for row in range(self.rowCount()):
            if self.item(row, 0).checkState() == Qt.Unchecked:
                continue
            data_sets.append(self._data_manager.data_sets[row])
        return data_sets


class MainWindow(QWidget):
    def __init__(self, *, data_manager):
        super().__init__()

        self.setWindowTitle('PDViPeR')
        self._data_sets_model = model = DataModel(data_manager, self)

        self._controls_panel = ControlsPanel(data_manager=data_manager)
        self._data_sets_table = QTableView()
        self._plot_window = PlotWindow(model=model)

        self._data_sets_table.setModel(self._data_sets_model)
        self._data_sets_table.setColumnWidth(0, 220)
        self._data_sets_table.setColumnWidth(1, 50)

        lhs_layout = QVBoxLayout()
        lhs_layout.addWidget(self._controls_panel)
        lhs_layout.addWidget(self._data_sets_table)
        lhs_widget = QWidget()

        lhs_widget.setLayout(lhs_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(lhs_widget)
        splitter.addWidget(self._plot_window)

        main_layout = QHBoxLayout(self)
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

        self.setGeometry(300, 300, 1200, 800)
        splitter.setSizes([450, 650])
