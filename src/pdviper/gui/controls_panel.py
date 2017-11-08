from PyQt5.QtWidgets import QWidget, QPushButton, QFileDialog, QVBoxLayout, QTabWidget
from PyQt5.QtCore import Qt


class ControlsPanel(QWidget):
    def __init__(self, parent=None, *, data_manager):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        tabs = QTabWidget(self)

        self._load_panel = LoadPanel(data_manager=data_manager)
        tabs.addTab(self._load_panel, 'Load')
        tabs.addTab(ProcessPanel(data_manager=data_manager), 'Process')
        tabs.addTab(QWidget(), 'Background')
        tabs.addTab(QWidget(), 'Transform')
        tabs.addTab(QWidget(), 'Peaks')

        layout.addWidget(tabs)
        self.setLayout(layout)


class LoadPanel(QWidget):
    def __init__(self, parent=None, *, data_manager):
        super().__init__(parent)
        self._data_manager = data_manager
        layout = QVBoxLayout()
        self._open_files_button = open_files_button = QPushButton('Open files...')
        open_files_button.clicked.connect(self._handle_open_files_button_click)
        layout.addWidget(open_files_button)
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)

    def _handle_open_files_button_click(self):
        file_names, _ = QFileDialog.getOpenFileNames(self, 'Open files', '',
                                                     'XYE files (*.xye)')
        self._data_manager.load(file_names)


class ProcessPanel(QWidget):
    def __init__(self, parent=None, *, data_manager):
        super().__init__(parent)
        self._load_partners_button = QPushButton('Load Partners')
        self._load_partners_button.clicked.connect(lambda: data_manager.load_partners())
        layout = QVBoxLayout()
        layout.addWidget(self._load_partners_button)
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)
