from pathlib import Path

from PyQt5.QtCore import Qt

from pdviper.gui.main_window import DataModel
from pdviper.data_manager import DataManager


fixtures_dir = Path(__file__).parent / '../fixtures'
TEST_FILE1 = str(fixtures_dir / 'file1.xye')
TEST_FILE2 = str(fixtures_dir / 'file2.xye')


def test_data_model_adds_rows():
    data_manager = DataManager()
    model = DataModel(data_manager, None)
    assert model.rowCount() == 0
    data_manager.load([TEST_FILE1])
    assert model.rowCount() == 1
    data_manager.load([TEST_FILE2])
    assert model.rowCount() == 2


def test_data_model_remembers_checked_state_when_rows_added():
    data_manager = DataManager()
    model = DataModel(data_manager, None)
    data_manager.load([TEST_FILE1])
    model.item(0, 0).setCheckState(Qt.Unchecked)
    data_manager.load([TEST_FILE2])
    assert model.item(0, 0).checkState() == Qt.Unchecked


def test_data_model_provides_active_data_sets():
    data_manager = DataManager()
    model = DataModel(data_manager, None)
    data_manager.load([TEST_FILE1, TEST_FILE2])
    model.item(0, 0).setCheckState(Qt.Unchecked)
    assert len(model.get_active_data_sets()) == 1
    assert model.get_active_data_sets()[0].name == 'file2'
