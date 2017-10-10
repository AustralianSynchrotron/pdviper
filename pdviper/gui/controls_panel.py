from PyQt5.QtWidgets import QGroupBox, QPushButton, QVBoxLayout


class ControlsPanel(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        button = QPushButton('Open files...')
        layout.addWidget(button)
        self.setLayout(layout)
