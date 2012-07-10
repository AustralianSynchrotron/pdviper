from enthought.etsconfig.api import ETSConfig

def fix_background_color():
    if ETSConfig.toolkit == 'wx':
        # Monkey-patch for incorrect window background on Ubuntu.
        import platform
        if platform.system() == 'Linux' and 'Ubuntu' in platform.version():
            from traitsui.wx import constants
            constants.WindowColor = constants.wx.Colour( 232, 232, 232 )
            #constants.WindowColor = constants.wx.SystemSettings_GetColour(constants.wx.SYS_COLOUR_WINDOW)

