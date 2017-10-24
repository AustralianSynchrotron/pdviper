from PyQt5.QtWidgets import QWidget, QPushButton, QFileDialog, QVBoxLayout, QTabWidget


class LoadPanel(QWidget):
    def __init__(self, parent=None, *, data_manager):
        super().__init__(parent)
        self._data_manager = data_manager
        layout = QVBoxLayout(self)
        self._open_files_button = open_files_button = QPushButton('Open files...')
        open_files_button.pressed.connect(self._handleOpenFilesButtonPress)
        layout.addWidget(open_files_button)
        self.setLayout(layout)

    def _handleOpenFilesButtonPress(self):
        file_names, _ = QFileDialog.getOpenFileNames(self, 'Open files', '',
                                                     'XYE files (*.xye)')
        self._data_manager.load(file_names)


class ControlsPanel(QWidget):
    def __init__(self, parent=None, *, data_manager):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        tabs = QTabWidget(self)

        self._load_panel = LoadPanel(self, data_manager=data_manager)
        tabs.addTab(self._load_panel, 'Load')
        tabs.addTab(QWidget(), 'Process')
        tabs.addTab(QWidget(), 'Background')
        tabs.addTab(QWidget(), 'Transform')
        tabs.addTab(QWidget(), 'Peaks')

        layout.addWidget(tabs)
        self.setLayout(layout)
