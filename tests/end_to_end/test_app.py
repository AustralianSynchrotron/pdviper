from pdviper import MainWindow


def test_application_loads(qtbot):
    gui = MainWindow()
    qtbot.addWidget(gui)
    assert gui.windowTitle() == 'PDViPeR'
