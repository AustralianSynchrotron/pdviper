from abc import ABC, abstractmethod


class XyPlotWidget(ABC):
    @abstractmethod
    def __init__(self, *, data_presenter):
        ...

    @abstractmethod
    def plot(self, preserve_zoom=True):
        ...

    @abstractmethod
    def reset_zoom(self):
        ...

    @abstractmethod
    def export_image(self, path, image_format):
        ...

    @property
    @abstractmethod
    def supported_image_formats(self):
        ...
