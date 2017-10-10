from PyQt5.QtWidgets import QApplication
import pandas as pd

from .gui import MainWindow


class DataSet:
    def __init__(self, path):
        self.source = path
        self._load_xye(path)

    def _load_xye(self, path):
        columns = ['angle', 'intensity', 'intensity_stdev']
        df = pd.read_csv(path, delimiter=' ', names=columns, index_col=False)
        self.angle = df.angle.values
        self.intensity = df.intensity.values
        self.intensity_stdev = df.intensity_stdev.values


class DataManager:
    def __init__(self):
        self.data_sets = []

    def load(self, paths):
        self.data_sets.extend(DataSet(p) for p in paths)


def main():
    app = QApplication([])
    main_window = MainWindow(data_manager=DataManager())
    main_window.show()
    app.exec_()
