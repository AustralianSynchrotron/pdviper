from enthought.etsconfig.api import ETSConfig


def fix_background_color():
    if ETSConfig.toolkit == 'wx':
        # Monkey-patch for incorrect window background on Ubuntu.
        import platform
        if platform.system() == 'Linux' and 'Ubuntu' in platform.version():
            from traitsui.wx import constants
            import pyface.api
            from pyface.ui.wx.system_metrics import SystemMetrics
            constants.WindowColor = constants.wx.Colour( 232, 232, 232 )
            class FixedSystemMetrics(SystemMetrics):
                def _get_dialog_background_color(self):
                    return (232/255., 232/255., 232/255.)
            pyface.api.SystemMetrics = FixedSystemMetrics


if ETSConfig.toolkit == 'wx':
    from traitsui.wx.color_editor import SimpleColorEditor, ToolkitEditorFactory

    class FixedColorEditor(SimpleColorEditor):
        def update_editor(self):
            super(FixedColorEditor, self).update_editor()
            name = self.control.GetValue()
            if name.startswith('rgb('):
                name = 'custom'
            self.control.SetStringSelection(name)

    class ColorEditor(ToolkitEditorFactory):
        def _get_simple_editor_class(self):
            return FixedColorEditor
else:
    from traitsui.api import ColorEditor

