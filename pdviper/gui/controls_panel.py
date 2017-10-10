from PyQt5.QtWidgets import QGroupBox, QPushButton, QFileDialog, QVBoxLayout


class ControlsPanel(QGroupBox):
    def __init__(self, parent=None, *, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        layout = QVBoxLayout(self)
        self.openFilesButton = openFilesButton = QPushButton('Open files...')
        openFilesButton.pressed.connect(self.handleOpenFilesButtonPress)
        layout.addWidget(openFilesButton)
        self.setLayout(layout)

    def handleOpenFilesButtonPress(self):
        fileNames, _ = QFileDialog.getOpenFileNames(self, 'Open files')
        self.data_manager.load(fileNames)
