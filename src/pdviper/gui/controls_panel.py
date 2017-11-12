from PyQt5.QtWidgets import QWidget, QPushButton, QFileDialog, QVBoxLayout, QTabWidget, \
                            QGroupBox, QRadioButton, QHBoxLayout, QButtonGroup
from PyQt5.QtCore import Qt

from pdviper.data_manager import MergePartners


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

    _merge_partners_options = [
        MergePartners.P1_2,
        MergePartners.P3_4,
        MergePartners.P12_34,
    ]
    _default_merge_partners_index = 0

    def __init__(self, parent=None, *, data_manager):
        super().__init__(parent)

        self._merge_partners = self._merge_partners_options[
            self._default_merge_partners_index
        ]

        self._load_partners_button = QPushButton('Load Partners')
        self._load_partners_button.clicked.connect(lambda: data_manager.load_partners())

        merge_partners_group = self._add_merge_patners_selections()
        self._combine_partners_button = QPushButton('Splice')
        self._combine_partners_button.clicked.connect(
            lambda: data_manager.merge_partners(self._merge_partners))

        layout = QVBoxLayout()
        layout.addWidget(self._load_partners_button)
        layout.addSpacing(15)
        layout.addWidget(merge_partners_group)
        layout.addWidget(self._combine_partners_button)
        layout.setAlignment(Qt.AlignTop)
        self.setLayout(layout)

    def _add_merge_patners_selections(self):

        layout = QHBoxLayout()
        self._merge_partners_group = group = QButtonGroup()
        for idx, merge_partners in enumerate(self._merge_partners_options):
            pos1, pos2 = merge_partners.value
            button = QRadioButton(f'p{pos1.value}+p{pos2.value}')
            layout.addWidget(button)
            group.addButton(button, idx)

        box = QGroupBox('Positions to Combine')
        box.setLayout(layout)
        group.buttonClicked[int].connect(self._handle_merge_partners_option_change)
        group.button(self._default_merge_partners_index).setChecked(True)
        return box

    def _handle_merge_partners_option_change(self, index):
        self._merge_partners = self._merge_partners_options[index]
