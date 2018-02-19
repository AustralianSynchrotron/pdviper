from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen

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
        self._zoom_rect = None
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
        self._update_zoom_rect(p0=(event.x, self._figure_height - event.y))

    def _on_mouse_move(self, event):
        if not self._mouse_clicked:
            return
        self._update_zoom_rect(p1=(event.x, self._figure_height - event.y))

    def _on_mouse_release(self, event):
        if not self._mouse_clicked:
            return
        self._mouse_clicked = False
        x0, _ = self._transform_display_to_data_coords(self._zoom_rect[:2])
        x1, _ = self._transform_display_to_data_coords(self._zoom_rect[2:])
        self._clear_zoom_rect()
        self._ax.set_xlim(x0, x1)
        self.draw()

    def _update_zoom_rect(self, *, p0=None, p1=None):
        if p0 is None:
            p0 = self._zoom_rect[:2]
        if p1 is None:
            p1 = p0
        self._zoom_rect = (*p0, *p1)
        self.update()

    def _clear_zoom_rect(self):
        self._zoom_rect = None
        self.update()

    def _transform_display_to_data_coords(self, point):
        return self._ax.transData.inverted().transform(point)

    def paintEvent(self, e):
        super().paintEvent(e)
        self._paint_zoom_rect()

    def _paint_zoom_rect(self):
        if self._zoom_rect is None:
            return
        painter = QPainter(self)
        painter.setPen(QPen(Qt.red, 5 / self._dpi_ratio, Qt.DotLine))
        painter.drawRect(*self._zoom_rect_for_qt)
        painter.end()

    @property
    def _zoom_rect_for_qt(self):
        x0, y0, x1, y1 = [pt / self._dpi_ratio for pt in self._zoom_rect]
        return x0, y0, x1 - x0, y1 - y0

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
        self._ax.set_autoscale_on(True)
        self._ax.autoscale_view()
        self.draw()
