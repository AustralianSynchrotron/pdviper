from collections import namedtuple

from PyQt5.QtChart import QChart, QChartView, QLineSeries
from PyQt5.QtCore import Qt, QPointF, QRectF

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
        if self.legend == XyLegendState.ON:
            chart.legend().setAlignment(Qt.AlignRight)
        else:
            chart.legend().setVisible(False)
        self.setChart(chart)

        x_axis = self._chart.axisX()
        y_axis = self._chart.axisY()

        if x_axis:
            if self._last_zoom:
                self._restore_zoom_range()
            else:
                self._handle_zoom_change()
            x_axis.rangeChanged.connect(self._handle_zoom_change)
            y_axis.rangeChanged.connect(self._handle_zoom_change)

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


verify_class_implements_abc(QtChartsXyPlotWidget, XyPlotWidget)
