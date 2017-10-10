from PyQt5.QtWidgets import QApplication

from .gui import MainWindow
from .data_manager import DataManager


def main():
    app = QApplication([])
    main_window = MainWindow(data_manager=DataManager())
    main_window.show()
    app.exec_()
