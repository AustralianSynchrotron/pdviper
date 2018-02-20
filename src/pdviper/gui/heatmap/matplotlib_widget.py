from PyQt5.QtGui import QPainter, QColor

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

import numpy as np


class MatplotlibHeatmapWidget(FigureCanvasQTAgg):

    def __init__(self, *, data_presenter):
        self._figure = Figure()
        super().__init__(self._figure)
        self._presenter = data_presenter
        self._ax = self._figure.add_subplot(111)
        self._image = None
        self._colorbar = None
        self._mouse_clicked = False
        self._zoom_limits = None
        self.mpl_connect('button_press_event', self._on_mouse_click)
        self.mpl_connect('button_release_event', self._on_mouse_release)
        self.mpl_connect('motion_notify_event', self._on_mouse_move)

    @property
    def _figure_height(self):
        return self.figure.bbox.height

    def _on_mouse_click(self, event):
        if event.inaxes != self._ax:
            return
        self._mouse_clicked = True
        self._set_zoom_limits(event.x, event.x)

    def _on_mouse_move(self, event):
        if not self._mouse_clicked:
            return
        self._set_zoom_limits(self._zoom_limits[0], event.x)

    def _on_mouse_release(self, event):
        if not self._mouse_clicked:
            return
        self._mouse_clicked = False
        x0, x1 = [self._transform_x_display_to_data_coord(x) for x in sorted(self._zoom_limits)]
        self._clear_zoom_limits()
        self._ax.set_xlim(x0, x1)
        self.draw()

    def _set_zoom_limits(self, start, end):
        self._zoom_limits = (start, end)
        self.update()

    def _clear_zoom_limits(self):
        self._zoom_limits = None
        self.update()

    def _transform_x_display_to_data_coord(self, x):
        return self._ax.transData.inverted().transform((x, 0))[0]

    def paintEvent(self, e):
        super().paintEvent(e)
        self._paint_zoom_rect()

    def _paint_zoom_rect(self):
        if self._zoom_limits is None:
            return
        painter = QPainter(self)
        painter.setPen(QColor(190, 190, 190, 255))
        painter.setBrush(QColor(190, 190, 190, 100))
        painter.drawRect(*self._zoom_rect_for_qt)
        painter.end()

    @property
    def _zoom_rect_for_qt(self):
        ax_height = self._ax.bbox.height
        _, y0 = self._ax.bbox.min
        y0 = self._figure_height - (y0 + ax_height) + 1
        x0, x1 = [x / self._dpi_ratio for x in sorted(self._zoom_limits)]
        return x0, y0, x1 - x0, ax_height

    def plot(self):

        if self._image is None:
            self._image = self._ax.matshow([[]], aspect='auto', extent=(0, 1, 0, 1),
                                           origin='lower')

        if len(self._presenter.data) == 0:
            self._image.set(data=[[]], extent=(0, 1, 0, 1))
            self.draw()
            return

        data = self._presenter.data

        self._image.set(data=data, extent=(0, data.shape[1], 0, data.shape[0]))
        self._ax.relim()

        if self._colorbar is not None:
            self._colorbar.remove()
        self._colorbar = self._figure.colorbar(self._image)
        self._ax.set(
            xlabel=self._presenter.x_axis_label,
            ylabel=self._presenter.y_axis_label,
            yticks=np.arange(data.shape[0])+0.5,
            yticklabels=np.arange(1, data.shape[0] + 1),
        )
        self._ax.xaxis.tick_bottom()

        self.draw()

    def reset_zoom(self):
        self._ax.autoscale()
        self.draw()
