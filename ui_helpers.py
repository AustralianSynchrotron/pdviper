import os
import subprocess
from pyface.api import FileDialog, OK

def get_save_as_xyz_filename(directory,filename):
    wildcard =   'XYZ (*.xyz)|*.xyz| All files (*.*)|*.*|'
    dialog = FileDialog(default_directory=directory,default_filename=filename,action='save as', title='Save as', wildcard=wildcard)
    if dialog.open() == OK:
        filename = dialog.path
        if filename:
            return filename
    return None

def get_save_as_filename():
    wildcard =  'PNG file (.png)|*.png|TIFF file (.tiff)|*.tiff|EPS file (.eps)|*.eps|SVG file (.svg)|*.svg|'
    dialog = FileDialog(action='save as', title='Save as', wildcard=wildcard)
    if dialog.open() == OK:
        filename = dialog.path
        if filename:
            return filename
    return None

def get_save_as_csv_filename():
    wildcard =  'CSV file (.csv)|*.csv|'
    dialog = FileDialog(action='save as', title='Save as', wildcard=wildcard)
    if dialog.open() == OK:
        filename = dialog.path
        if filename:
            return filename
    return None

xye_wildcard = 'XYE (*.xye)|*.xye|' \
           'XY (*.xy)|*.xy|' \
           'DAT (*.dat)|*.dat|'\
           'RAW (*.raw)|*.raw|'\
           'All files (*.*)|*.*|'

def get_file_list_from_dialog():
    dlg = FileDialog(title='Choose files', action='open files', wildcard=xye_wildcard)
    if dlg.open() == OK:
        return dlg.paths
    return []

def get_file_from_dialog():
    dlg = FileDialog(title='Choose file', action='open', wildcard=xye_wildcard)
    if dlg.open() == OK:
        return dlg.paths[0]
    return None

def open_file_with_default_handler(filename):
    startfile(filename)

def open_file_dir_with_default_handler(filename):
    startfile(os.path.split(filename)[0])


def get_transformed_filename(filename):
    dialog = FileDialog(default_path=filename, action='save as', title='Save as', wildcard=xye_wildcard)
    if dialog.open() == OK:
        filename = dialog.path
        if filename:
            return filename
    return None

def get_txt_filename(path):
    wildcard =   'txt (*.txt)|*.txt| All files (*.*)|*.*|'
    dialog = FileDialog(default_path=path, action='save as', title='Save as', wildcard=wildcard)
    if dialog.open() == OK:
        filename = dialog.path
        if filename:
            return filename
    return None
    
def startfile(filename):
    try:
        os.startfile(filename)
    except:
        subprocess.Popen(['xdg-open', filename])
