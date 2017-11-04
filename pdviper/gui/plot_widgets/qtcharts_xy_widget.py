from collections import namedtuple

from PyQt5.QtChart import QChart, QChartView, QLineSeries
from PyQt5.QtCore import QPointF, QRectF

from .xy_widget import XyPlotWidget, XyLegendState, verify_class_implements_abc


Zoom = namedtuple('Zoom', 'x1 x2 y1 y2')


class QtChartsXyPlotWidget(QChartView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRubberBand(QChartView.RectangleRubberBand)
        self.data_sets = []
        self.legend = XyLegendState.OFF
        self._chart = None
        self._last_zoom = None

    def plot(self):
        self._chart = chart = QChart()
        for ds in self.data_sets:
            series = QLineSeries(chart)
            for x, y in zip(ds.angle, ds.intensity):
                series.append(QPointF(x, y))
            series.setName(ds.name)
            chart.addSeries(series)
        chart.createDefaultAxes()
        self.setChart(chart)
        self._draw_legend()

        x_axis = self._chart.axisX()
        y_axis = self._chart.axisY()

        if x_axis:
            if self._last_zoom:
                self._restore_zoom_range()
            else:
                self._handle_zoom_change()
            x_axis.rangeChanged.connect(self._handle_zoom_change)
            y_axis.rangeChanged.connect(self._handle_zoom_change)

    def _draw_legend(self):
        if not self._chart:
            return
        if self.legend == XyLegendState.ON:
            inset_x = width = 310
            inset_y = 30
            legend = self._chart.legend()
            legend.detachFromChart()
            loc = self.geometry().topRight() - QPointF(inset_x, inset_y)
            height = self.geometry().height()
            legend.setGeometry(QRectF(loc.x(), loc.y(), width, height))
            legend.update()
        else:
            self._chart.legend().setVisible(False)

    def reset_zoom(self):
        if self._chart:
            self._chart.zoomReset()

    def _handle_zoom_change(self, *args):
        x_axis = self._chart.axisX()
        y_axis = self._chart.axisY()
        self._last_zoom = Zoom(x_axis.min(), x_axis.max(), y_axis.min(), y_axis.max())

    def _restore_zoom_range(self):
        if self._last_zoom is None:
            return
        x1, x2, y1, y2 = self._last_zoom
        series = self._chart.series()[-1]
        p1 = self._chart.mapToPosition(QPointF(x1, y1), series)
        p2 = self._chart.mapToPosition(QPointF(x2, y2), series)
        x = min(p1.x(), p2.x())
        y = min(p1.y(), p2.y())
        width = abs(p1.x() - p2.x())
        height = abs(p1.y() - p2.y())
        rect = QRectF(x, y, width, height)
        self._chart.zoomIn(rect)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._draw_legend()


verify_class_implements_abc(QtChartsXyPlotWidget, XyPlotWidget)
