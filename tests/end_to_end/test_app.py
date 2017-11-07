import pytest

from PyQt5.QtCore import Qt

from pdviper import MainWindow
from pdviper import DataManager
from pdviper.gui.controls_panel import QFileDialog

from tests.fixtures import TEST_FILE1


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
    mocker.patch.object(QFileDialog, 'getOpenFileNames',
                        return_value=([TEST_FILE1], None))
    qtbot.mouseClick(gui._controls_panel._load_panel._open_files_button, Qt.LeftButton)
    assert len(data_manager.data_sets) == 1
    data_set = data_manager.data_sets[0]
    assert data_set.name == 'file1'
    assert len(data_set.angle) == 19890
    assert list(data_set.angle[:3]) == [3.01002, 3.01378, 3.01753]
    assert list(data_set.intensity[:3]) == [5096.21, 5060.57, 4973.6]
    assert list(data_set.intensity_stdev[:3]) == [67.053, 68.1375, 69.2789]


def test_loading_xye_file_triggers_plot(gui, data_manager, qtbot, mocker):
    plot = mocker.patch.object(gui._visualisation_panel, '_plot', autospec=True)
    data_manager.load([TEST_FILE1])
    assert plot.called is True
