from abc import ABC, abstractmethod


class XyPlotWidget(ABC):
    @abstractmethod
    def plot(self):
        ...

    @abstractmethod
    def reset_zoom(self):
        ...
