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
        pass
