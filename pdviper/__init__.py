from PyQt5.QtWidgets import QApplication

from .gui import MainWindow


class DataManager:
    def __init__(self):
        self.data_sets = []

    def load(self, paths):
        self.data_sets.extend(paths)


def main():
    app = QApplication([])
    main_window = MainWindow(data_manager=DataManager())
    main_window.show()
    app.exec_()
