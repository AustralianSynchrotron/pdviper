from unittest.mock import create_autospec

from PyQt5.QtCore import Qt

from pdviper.gui.controls_panel import ProcessPanel
from pdviper.data_manager import DataManager


def test_load_partners_button_loads_partners(qtbot):
    data_manager_mock = create_autospec(DataManager, instance=True)
    panel = ProcessPanel(data_manager=data_manager_mock)
    qtbot.addWidget(panel)
    qtbot.mouseClick(panel._load_partners_button, Qt.LeftButton)
    assert data_manager_mock.load_partners.called is True
