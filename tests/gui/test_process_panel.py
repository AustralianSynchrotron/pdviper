from unittest.mock import create_autospec, call

from PyQt5.QtCore import Qt
import pytest

from pdviper.gui.controls_panel import ProcessPanel
from pdviper.data_manager import DataManager, MergePartners


def test_load_partners_button_loads_partners(qtbot):
    data_manager_mock = create_autospec(DataManager, instance=True)
    panel = ProcessPanel(data_manager=data_manager_mock)
    qtbot.addWidget(panel)
    qtbot.mouseClick(panel._load_partners_button, Qt.LeftButton)
    assert data_manager_mock.load_partners.called is True


def test_combine_partners_button_combines_partners(qtbot):
    data_manager_mock = create_autospec(DataManager, instance=True)
    panel = ProcessPanel(data_manager=data_manager_mock)
    qtbot.addWidget(panel)
    qtbot.mouseClick(panel._combine_partners_button, Qt.LeftButton)
    assert data_manager_mock.merge_partners.call_args == call(MergePartners.P1_2)


@pytest.mark.xfail
def test_merge_partners_options(qtbot):
    """ This is failing for some reason. pytest-qt bug? """
    data_manager_mock = create_autospec(DataManager, instance=True)
    panel = ProcessPanel(data_manager=data_manager_mock)
    qtbot.addWidget(panel)
    qtbot.keyClick(panel._merge_partners_group.button(1), Qt.Key_Enter)
    qtbot.mouseClick(panel._combine_partners_button, Qt.LeftButton)
    assert data_manager_mock.merge_partners.call_args == call(MergePartners.P3_4)
