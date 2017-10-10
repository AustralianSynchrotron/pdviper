from PyQt5.QtWidgets import QWidget


class PlotWindow(QWidget):
    def __init__(self, parent=None, *, data_manager):
        super().__init__(parent)
        self._data_manager = data_manager
        data_manager.add_callback(self.handleDataManagerUpdate)

    def handleDataManagerUpdate(self):
        self.plot()

    def plot(self):
        pass
