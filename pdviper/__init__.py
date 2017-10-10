from PyQt5.QtWidgets import QApplication

from .gui import MainWindow


def main():
    app = QApplication([])
    main_window = MainWindow()
    main_window.show()
    app.exec_()
