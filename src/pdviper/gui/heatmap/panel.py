from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSignal

from ..utils import ImageFormat
from .presenter import HeatmapDataPresenter


class HeatmapPanel(QWidget):
    def __init__(self, PlotWidgetCls):
        super().__init__()
        self._presenter = HeatmapDataPresenter()
        self._plot_widget = PlotWidgetCls(data_presenter=self._presenter)
        self._controls = controls = HeatmapPlotControls(
            data_presenter=self._presenter,
            image_formats=self._plot_widget.supported_image_formats,
        )
        controls.zoom_reset.connect(self._plot_widget.reset_zoom)
        controls.export_image.connect(self._plot_widget.export_image)
        layout = QVBoxLayout()
        layout.addWidget(controls)
        layout.addWidget(self._plot_widget)
        self.setLayout(layout)

    def plot(self, data_sets):
        self._presenter.data_sets = data_sets
        self._plot_widget.plot()


class HeatmapPlotControls(QWidget):

    zoom_reset = pyqtSignal()
    export_image = pyqtSignal(str, ImageFormat)

    def __init__(self, parent=None, *, data_presenter, image_formats):
        super().__init__(parent)

        self._image_formats = image_formats

        reset_zoom = QPushButton('Reset zoom')
        reset_zoom.clicked.connect(self.zoom_reset)

        self._save_image_button = save_image_button = QPushButton('Save to file')
        if not image_formats:
            self._save_image_button.setEnabled(False)
        save_image_button.clicked.connect(self._save_image)

        layout = QHBoxLayout()
        layout.addWidget(reset_zoom)
        layout.addWidget(save_image_button)

        self.setLayout(layout)

    def _save_image(self):
        filters = ';;'.join(fmt.qt_filter for fmt in self._image_formats)
        destination, chosen_fltr = QFileDialog.getSaveFileName(self, 'Save image', '', filters)
        format_ = next(fmt for fmt in self._image_formats if fmt.qt_filter == chosen_fltr)
        self.export_image.emit(destination, format_)
