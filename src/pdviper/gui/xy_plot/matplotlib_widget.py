from PyQt5.QtGui import QPainter, QColor

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from .options import XyLegendState
from ...constants import MouseButton


class MatplotlibXyPlotWidget(FigureCanvasQTAgg):

    def __init__(self, *, data_presenter):
        self._figure = Figure()
        super().__init__(self._figure)
        self.legend = XyLegendState.OFF
        self._presenter = data_presenter
        self._ax = self._figure.add_subplot(111)
        self._mouse_clicked = False
        self._zoom_box_limits = None
        self._user_axes_limits = None
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
        self._set_zoom_box_limits(event.x, event.x)

    def _zoom_out(self, event):
        x_min, x_max = self._presenter.x_range
        if x_min is None:
            return
        current_x_min, current_x_max = self._ax.get_xlim()
        current_x_span = current_x_max - current_x_min
        new_x_min = max(current_x_min - current_x_span, x_min)
        new_x_max = max(min(current_x_max + current_x_span, x_max), new_x_min)
        self._ax.set_xlim(new_x_min, new_x_max)
        self.draw()

    def _on_mouse_move(self, event):
        if not self._mouse_clicked:
            return
        self._set_zoom_box_limits(self._zoom_box_limits[0], event.x)

    def _on_mouse_release(self, event):
        if not self._mouse_clicked:
            return
        self._mouse_clicked = False
        if self._zoom_box_limits[0] != self._zoom_box_limits[1]:
            self._ax.set_xlim(*self._zoom_box_limits_in_data_coordinates)
            self._user_axes_limits = self._zoom_box_limits
        self._clear_zoom_box_limits()
        self.draw()

    def _set_zoom_box_limits(self, start, end):
        self._zoom_box_limits = (start, end)
        self.update()

    def _clear_zoom_box_limits(self):
        self._zoom_box_limits = None
        self.update()

    @property
    def _zoom_box_limits_in_data_coordinates(self):
        display_to_data_transform = self._ax.transData.inverted().transform
        return [display_to_data_transform((x, 0))[0] for x in sorted(self._zoom_box_limits)]

    def paintEvent(self, e):
        super().paintEvent(e)
        self._paint_zoom_rect()

    def _paint_zoom_rect(self):
        if self._zoom_box_limits is None:
            return
        painter = QPainter(self)
        painter.setPen(QColor(190, 190, 190, 255))
        painter.setBrush(QColor(190, 190, 190, 100))
        painter.drawRect(*self._zoom_rect_for_qt)
        painter.end()

    @property
    def _zoom_rect_for_qt(self):
        y0 = self._figure_height - self._ax.transAxes.transform((0, 1))[1] + 1
        x0, x1 = sorted(self._zoom_box_limits)
        return self._scale_to_dpi(x0, y0, x1 - x0, self._axes_height)

    def _scale_to_dpi(self, *values):
        return tuple(v / self._dpi_ratio for v in values)

    def plot(self, preserve_zoom=True):

        init_xlim = self._ax.get_xlim()
        init_ylim = self._ax.get_ylim()

        self._ax.clear()
        for series in self._presenter.series:
            self._ax.plot(series.x, series.y, label=series.name)

        self._ax.set(
            xlabel=self._presenter.x_axis_label,
            ylabel=self._presenter.y_axis_label,
        )

        if self._user_axes_limits is not None and preserve_zoom:
            self._ax.set_xlim(*init_xlim)
            self._ax.set_ylim(*init_ylim)

        if self.legend == XyLegendState.ON:
            self._ax.legend()

        self.draw()

    def reset_zoom(self):
        self._user_axes_limits = None
        self._ax.autoscale()
        self.draw()
