import sys
import signal

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer

from .gui import MainWindow
from .data_manager import DataManager


def _close_on_ctrl_c(app):
    signal.signal(signal.SIGINT, lambda *_: app.quit())
    # allow the python interpreter to be called so signals will be processed:
    timer = QTimer(app)
    timer.start(100)
    timer.timeout.connect(lambda: None)


def main():
    app = QApplication([])
    data_manager = DataManager()
    main_window = MainWindow(data_manager=data_manager)
    main_window.show()
    data_manager.load(sys.argv[1:])
    _close_on_ctrl_c(app)
    app.exec_()
