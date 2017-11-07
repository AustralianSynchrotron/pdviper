from PyQt5.QtWidgets import QTableView
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QSysInfo, pyqtSignal


def is_delete_key(key):
    if key == Qt.Key_Delete:
        return True
    elif QSysInfo().productType() == 'osx' and key == Qt.Key_Backspace:
        return True
    else:
        return False


class DataSetsTable(QTableView):
    def __init__(self, parent=None, *, model):
        super().__init__(parent)
        self.setModel(model)
        self.setColumnWidth(0, 300)

    def keyPressEvent(self, event):
        if is_delete_key(event.key()):
            self.model().delete_items(self.selectedIndexes())


class DataSetsModel(QStandardItemModel):

    changed = pyqtSignal()

    def __init__(self, data_manager, parent):
        super().__init__(0, 1, parent)
        self._data_manager = data_manager
        data_manager.add_observer(self)
        self.setHeaderData(0, Qt.Horizontal, 'Name')
        self._updating = False
        self.itemChanged.connect(self._handle_item_changed)

    def data_sets_added(self, indexes):
        self._updating = True
        for row in indexes:
            ds = self._data_manager.data_sets[row]
            item = QStandardItem(ds.name)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self.setItem(row, 0, item)
        self._updating = False
        self.changed.emit()

    def data_sets_removed(self, indexes):
        for index in reversed(indexes):
            self.removeRow(index)
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

    def delete_items(self, table_indexes):
        self._data_manager.remove([index.row() for index in table_indexes])
