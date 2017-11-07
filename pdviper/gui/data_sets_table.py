from PyQt5.QtWidgets import QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, pyqtSignal


class DataSetsTable(QTableView):
    def __init__(self, parent=None, *, model):
        super().__init__(parent)
        self.setModel(model)
        self.setColumnWidth(0, 300)


class DataSetsModel(QStandardItemModel):

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

    def get_active_data_sets(self):
        data_sets = []
        for row in range(self.rowCount()):
            if self.item(row, 0).checkState() == Qt.Unchecked:
                continue
            data_sets.append(self._data_manager.data_sets[row])
        return data_sets
