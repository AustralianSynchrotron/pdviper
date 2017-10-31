from PyQt5.QtChart import QChart, QChartView, QLineSeries
from PyQt5.QtCore import Qt, QPointF

from .xy_widget import XyPlotWidget, XyLegendState, verify_class_implements_abc


class QtChartsXyPlotWidget(QChartView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRubberBand(QChartView.RectangleRubberBand)
        self.data_sets = []
        self.legend = XyLegendState.OFF

    def plot(self):
        chart = QChart()
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


verify_class_implements_abc(QtChartsXyPlotWidget, XyPlotWidget)
