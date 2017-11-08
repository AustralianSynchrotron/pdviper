from unittest.mock import create_autospec, Mock

import pytest

from pdviper.gui.data_sets_table import DataSetsTable, DataSetsModel
from pdviper.data_manager import DataManager, DataSet

from PyQt5.QtCore import Qt


@pytest.fixture
def data_manager_mock():
    data_manager_mock = create_autospec(DataManager)
    yield data_manager_mock


@pytest.fixture
def model(data_manager_mock):
    yield DataSetsModel(data_manager_mock, None)


@pytest.fixture
def table(qtbot, model):
    table = DataSetsTable(model=model)
    qtbot.addWidget(table)
    yield table


def add_data_set(data_manager_mock, model):
    data_manager_mock.data_sets = [create_data_set('ds1')]
    model.data_sets_added([0])


def create_data_set(name):
    return DataSet(name=name, angle=[], intensity=[], intensity_stdev=[])


def test_data_sets_table_handles_delete(data_manager_mock, model, table, qtbot):
    add_data_set(data_manager_mock, model)
    table.selectRow(0)
    qtbot.keyPress(table, Qt.Key_Delete)
    data_manager_mock.remove.assert_called_with([0])


def test_backspace_deletes_rows_on_osx(data_manager_mock, model, table, qtbot, mocker):
    QSysInfoMock = mocker.patch('pdviper.gui.data_sets_table.QSysInfo', autospec=True)
    QSysInfoMock.return_value.productType.return_value = 'osx'
    add_data_set(data_manager_mock, model)
    table.selectRow(0)
    qtbot.keyPress(table, Qt.Key_Backspace)
    data_manager_mock.remove.assert_called_with([0])


def test_data_sets_model_updates_data_set_name(model, data_manager_mock):
    add_data_set(data_manager_mock, model)
    slot = Mock()
    model.changed.connect(slot)
    model.item(0, 0).setData('new-name', Qt.EditRole)
    assert data_manager_mock.data_sets[0].name == 'new-name'
    assert slot.called is True
