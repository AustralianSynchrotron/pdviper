from pyface.api import FileDialog, OK


def get_save_as_filename():
    wildcard =  'PNG file (.png)|*.png|TIFF file (.tiff)|*.tiff|EPS file (.eps)|*.eps|SVG file (.svg)|*.svg|'
    dialog = FileDialog(action='save as', title='Save as', wildcard=wildcard)
    if dialog.open() == OK:
        filename = dialog.path
        if filename:
            return filename
    return None

def get_file_list_from_dialog():
    wildcard = 'XYE (*.xye)|*.xye|' \
               'All files (*.*)|*.*'
    dlg = FileDialog(title='Choose files', action='open files', wildcard=wildcard)
    if dlg.open() == OK:
        return dlg.paths
    return []

def open_file_with_default_handler(filename):
    try:
        import webbrowser
        webbrowser.open_new_tab(filename)
    except:
        pass

