from unittest.mock import call, ANY

import pytest

from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5.QtCore import Qt

from pdviper.gui.heatmap.panel import HeatmapPanel
from pdviper.gui.heatmap.abstract_widget import HeatmapWidget
from pdviper.gui.utils import verify_class_implements_abc, ImageFormat


IMG_FMT1 = ImageFormat('name1', 'ext1')
IMG_FMT2 = ImageFormat('name2', 'ext2')


class WidgetMock(QWidget):

    supported_image_formats = [IMG_FMT1, IMG_FMT2]

    def __init__(self, *, data_presenter):
        super().__init__()

    def plot(self): ...

    def reset_zoom(self): ...

    def export_image(self, path, image_format): ...


verify_class_implements_abc(WidgetMock, HeatmapWidget)


@pytest.fixture
def mock_getSaveFileName(mocker):
    yield mocker.patch.object(QFileDialog, 'getSaveFileName', return_value=('/dest1', None))


def test_heatmap_panel_enables_saving_figure(qtbot, mocker, mock_getSaveFileName):
    mocker.patch.object(WidgetMock, 'export_image', autospec=True)
    selected_path = '/tmp/imagename1.png'
    selected_filter = 'name1 (*.ext1)'
    mock_getSaveFileName.configure_mock(return_value=(selected_path, selected_filter))
    panel = HeatmapPanel(WidgetMock)
    plot_widget = panel._plot_widget
    qtbot.addWidget(panel)
    qtbot.mouseClick(panel._controls._save_image_button, Qt.LeftButton)
    filter_ = 'name1 (*.ext1);;name2 (*.ext2)'
    assert mock_getSaveFileName.call_args == call(ANY, ANY, ANY, filter_)
    assert plot_widget.export_image.call_args == call(plot_widget, selected_path, IMG_FMT1)


def test_heatmap_panel_enables_selecting_other_formats(qtbot, mocker, mock_getSaveFileName):
    mocker.patch.object(WidgetMock, 'export_image', autospec=True)
    selected_path = '/tmp/imagename1.png'
    selected_filter = 'name2 (*.ext2)'
    mock_getSaveFileName.configure_mock(return_value=(selected_path, selected_filter))
    panel = HeatmapPanel(WidgetMock)
    plot_widget = panel._plot_widget
    qtbot.addWidget(panel)
    qtbot.mouseClick(panel._controls._save_image_button, Qt.LeftButton)
    assert plot_widget.export_image.call_args == call(plot_widget, selected_path, IMG_FMT2)


def test_heatmap_panel_with_no_image_formats(qtbot, mocker):
    mocker.patch.object(WidgetMock, 'supported_image_formats', [])
    mocker.patch.object(WidgetMock, 'export_image', autospec=True)
    panel = HeatmapPanel(WidgetMock)
    qtbot.addWidget(panel)
    qtbot.mouseClick(panel._controls._save_image_button, Qt.LeftButton)
    assert panel._plot_widget.export_image.called is False
