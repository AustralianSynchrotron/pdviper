from PyQt5.QtChart import QChart, QChartView, QLineSeries
from PyQt5.QtCore import Qt, QPointF


class QtChartsXyPlotWidget(QChartView):
    def __init__(self):
        super().__init__()
        self.setRubberBand(QChartView.RectangleRubberBand)

    def plot(self, data_sets):
        chart = QChart()
        for ds in data_sets:
            series = QLineSeries(chart)
            for x, y in zip(ds.angle, ds.intensity):
                series.append(QPointF(x, y))
            series.setName(ds.name)
            chart.addSeries(series)
        chart.createDefaultAxes()
        chart.legend().setAlignment(Qt.AlignRight)
        self.setChart(chart)
