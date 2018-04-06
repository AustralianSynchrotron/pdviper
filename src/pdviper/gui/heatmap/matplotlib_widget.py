from enum import IntEnum

from PyQt5.QtGui import QPainter, QColor

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

import numpy as np


class MouseButton:
    LEFT = 1
    MIDDLE = 2
    RIGHT = 3


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

    @property
    def _axes_height(self):
        return self._ax.bbox.height

    def _on_mouse_click(self, event):
        if event.inaxes != self._ax:
            return
        if event.button == MouseButton.LEFT:
            self._start_zoom_selection(event)
        elif event.button == MouseButton.RIGHT:
            self._zoom_out(event)

    def _start_zoom_selection(self, event):
        self._mouse_clicked = True
        self._set_zoom_limits(event.x, event.x)

    def _zoom_out(self, event):
        x_min, x_max = self._presenter.x_range
        if x_min is None:
            return
        current_x_min, current_x_max = self._ax.get_xlim()
        current_x_span = current_x_max - current_x_min
        new_x_min = max(current_x_min - current_x_span, x_min)
        new_x_max = min(current_x_max + current_x_span, x_max)
        self._ax.set_xlim(new_x_min, new_x_max)
        self.draw()

    def _on_mouse_move(self, event):
        if not self._mouse_clicked:
            return
        self._set_zoom_limits(self._zoom_limits[0], event.x)

    def _on_mouse_release(self, event):
        if not self._mouse_clicked:
            return
        self._mouse_clicked = False
        if self._zoom_limits[0] != self._zoom_limits[1]:
            self._ax.set_xlim(*self._zoom_limits_in_data_coordinates)
        self._clear_zoom_limits()
        self.draw()

    def _set_zoom_limits(self, start, end):
        self._zoom_limits = (start, end)
        self.update()

    def _clear_zoom_limits(self):
        self._zoom_limits = None
        self.update()

    @property
    def _zoom_limits_in_data_coordinates(self):
        display_to_data_transform = self._ax.transData.inverted().transform
        return [display_to_data_transform((x, 0))[0] for x in sorted(self._zoom_limits)]

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
        y0 = self._figure_height - self._ax.transAxes.transform((0, 1))[1] + 1
        x0, x1 = sorted(self._zoom_limits)
        return self._scale_to_dpi(x0, y0, x1 - x0, self._axes_height)

    def _scale_to_dpi(self, *values):
        return tuple(v / self._dpi_ratio for v in values)

    def plot(self):

        if self._image is None:
            self._image = self._ax.matshow([[]], aspect='auto', extent=(0, 1, 0, 1),
                                           origin='lower')

        if len(self._presenter.data) == 0:
            self._image.set(data=[[]], extent=(0, 1, 0, 1))
            self.draw()
            return

        data = self._presenter.data

        self._image.set(data=data, extent=(*self._presenter.x_range, 0, data.shape[0]))
        self._ax.relim()

        if self._colorbar is not None:
            self._colorbar.remove()
        self._colorbar = self._figure.colorbar(self._image)
        self._ax.set(
            xlabel=self._presenter.x_axis_label,
            ylabel=self._presenter.y_axis_label,
            yticks=np.arange(data.shape[0]) + 0.5,
            yticklabels=np.arange(1, data.shape[0] + 1),
        )
        self._ax.xaxis.tick_bottom()

        self.draw()

    def reset_zoom(self):
        self._ax.autoscale()
        self.draw()
