from abc import ABC, abstractmethod


class HeatmapWidget(ABC):
    @abstractmethod
    def __init__(self, *, data_presenter):
        ...

    @abstractmethod
    def plot(self):
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
