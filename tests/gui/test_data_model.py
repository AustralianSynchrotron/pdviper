from unittest.mock import Mock

from PyQt5.QtCore import Qt

import pytest

from pdviper.gui.data_sets_table import DataSetsModel
from pdviper.data_manager import DataManager

from tests.fixtures import TEST_FILE1, TEST_FILE2


@pytest.fixture
def data_manager():
    yield DataManager()


@pytest.fixture
def model(data_manager):
    yield DataSetsModel(data_manager, None)


def test_data_model_adds_rows(data_manager, model):
    assert model.rowCount() == 0
    data_manager.load([TEST_FILE1])
    assert model.rowCount() == 1
    data_manager.load([TEST_FILE2])
    assert model.rowCount() == 2


def test_data_model_remembers_checked_state_when_rows_added(data_manager, model):
    data_manager.load([TEST_FILE1])
    model.item(0, 0).setCheckState(Qt.Unchecked)
    data_manager.load([TEST_FILE2])
    assert model.item(0, 0).checkState() == Qt.Unchecked


def test_data_model_provides_active_data_sets(data_manager, model):
    data_manager.load([TEST_FILE1, TEST_FILE2])
    model.item(0, 0).setCheckState(Qt.Unchecked)
    assert len(model.get_active_data_sets()) == 1
    assert model.get_active_data_sets()[0].name == 'file2'


def test_data_model_emits_changed_when_rows_added(data_manager, model):
    slot = Mock()
    model.changed.connect(slot)
    data_manager.load([TEST_FILE1])
    assert slot.called is True


def test_data_model_emits_single_changed_event_for_load(data_manager, model):
    slot = Mock()
    model.changed.connect(slot)
    data_manager.load([TEST_FILE1, TEST_FILE2])
    assert slot.call_count == 1


def test_data_model_removes_single_data_sets(data_manager, model):
    data_manager.load([TEST_FILE1, TEST_FILE2])
    assert model.rowCount() == 2
    data_manager.remove([0])
    assert model.rowCount() == 1
    assert model.item(0, 0).text() == 'file2'


def test_data_model_remove_data_set_preserves_check_states(data_manager, model):
    data_manager.load([TEST_FILE1, TEST_FILE2])
    model.item(1, 0).setCheckState(Qt.Unchecked)
    data_manager.remove([0])
    assert model.item(0, 0).checkState() == Qt.Unchecked


def test_data_model_removes_multiple_data_sets(data_manager, model):
    data_manager.load([TEST_FILE1, TEST_FILE2])
    assert model.rowCount() == 2
    data_manager.remove([0, 1])
    assert model.rowCount() == 0


def test_data_model_emits_signal_when_data_sets_are_removed(data_manager, model):
    data_manager.load([TEST_FILE1, TEST_FILE2])
    slot = Mock()
    model.changed.connect(slot)
    data_manager.remove([0, 1])
    assert slot.call_count == 1
