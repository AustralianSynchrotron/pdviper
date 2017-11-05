from abc import ABC, abstractmethod


class XyPlotWidget(ABC):
    @abstractmethod
    def plot(self, preserve_zoom=True):
        ...

    @abstractmethod
    def reset_zoom(self):
        ...
