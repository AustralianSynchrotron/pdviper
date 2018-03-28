from PyQt5.QtWidgets import QApplication
import sys

from .gui import MainWindow
from .data_manager import DataManager


def main():
    app = QApplication([])
    data_manager = DataManager()
    main_window = MainWindow(data_manager=data_manager)
    main_window.show()
    data_manager.load(sys.argv[1:])
    app.exec_()
