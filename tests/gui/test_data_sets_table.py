from unittest.mock import create_autospec

from pdviper.gui.data_sets_table import DataSetsTable, DataSetsModel
from pdviper.data_manager import DataManager, DataSet

from PyQt5.QtCore import Qt


def create_data_set(name):
    return DataSet(name=name, angle=[], intensity=[], intensity_stdev=[])


def test_data_sets_table_handles_delete(qtbot):
    data_manager_mock = create_autospec(DataManager)
    data_manager_mock.data_sets = [create_data_set('ds1')]
    model = DataSetsModel(data_manager_mock, None)
    table = DataSetsTable(model=model)
    qtbot.addWidget(table)
    model.data_sets_added([0])
    table.selectRow(0)
    qtbot.keyPress(table, Qt.Key_Delete)
    data_manager_mock.remove.assert_called_with([0])


def test_backspace_deletes_rows_on_osx(qtbot, mocker):
    QSysInfoMock = mocker.patch('pdviper.gui.data_sets_table.QSysInfo', autospec=True)
    QSysInfoMock.return_value.productType.return_value = 'osx'
    data_manager_mock = create_autospec(DataManager)
    data_manager_mock.data_sets = [create_data_set('ds1')]
    model = DataSetsModel(data_manager_mock, None)
    table = DataSetsTable(model=model)
    qtbot.addWidget(table)
    model.data_sets_added([0])
    table.selectRow(0)
    qtbot.keyPress(table, Qt.Key_Backspace)
    data_manager_mock.remove.assert_called_with([0])
