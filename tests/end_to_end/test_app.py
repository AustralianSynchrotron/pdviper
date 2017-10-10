from pathlib import Path

import pytest

from PyQt5.QtCore import Qt

from pdviper import MainWindow
from pdviper import DataManager
from pdviper.gui.controls_panel import QFileDialog


@pytest.fixture
def data_manager():
    yield DataManager()


@pytest.fixture
def gui(qtbot, data_manager):
    gui = MainWindow(data_manager=data_manager)
    qtbot.addWidget(gui)
    yield gui


def test_application_loads(gui):
    assert gui.windowTitle() == 'PDViPeR'


def test_can_load_xye_file(gui, data_manager, qtbot, mocker):
    file_path = Path(__file__).parent / '../fixtures/file1.xye'
    mocker.patch.object(QFileDialog, 'getOpenFileNames',
                        return_value=([str(file_path)], None))
    qtbot.mouseClick(gui.controlsPanel.openFilesButton, Qt.LeftButton)
    assert len(data_manager.data_sets) == 1
    data_set = data_manager.data_sets[0]
    assert data_set.source == str(file_path)
    assert len(data_set.angle) == 19890
    assert list(data_set.angle[:3]) == [3.01002, 3.01378, 3.01753]
    assert list(data_set.intensity[:3]) == [5096.21, 5060.57, 4973.6]
    assert list(data_set.intensity_stdev[:3]) == [67.053, 68.1375, 69.2789]
