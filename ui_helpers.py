import os
import subprocess
from pyface.api import FileDialog, OK
from PySide import QtGui
from traits.api import  HasTraits, Enum, Directory
from traitsui.api import View, Item,VGroup, Label, EnumEditor, DirectoryEditor
from traitsui.menu import OKButton, CancelButton

def get_save_as_xyz_filename(directory,filename):
    wildcard =   'XYZ (*.xyz)|*.xyz| All files (*.*)|*.*'
    dialog = FileDialog(default_directory=directory,default_filename=filename,action='save as', title='Save as', wildcard=wildcard)
    if dialog.open() == OK:
        filename = dialog.path
        if filename:
            return filename
    return None

def get_save_as_filename():
    wildcard =  'PNG file (.png)|*.png|TIFF file (.tiff)|*.tiff|EPS file (.eps)|*.eps|SVG file (.svg)|*.svg'
    dialog = FileDialog(action='save as', title='Save as', wildcard=wildcard)
    if dialog.open() == OK:
        filename = dialog.path
        if filename:
            return filename
    return None

def get_save_as_csv_filename():
    wildcard =  'CSV file (.csv)|*.csv'
    dialog = FileDialog(action='save as', title='Save as', wildcard=wildcard)
    if dialog.open() == OK:
        filename = dialog.path
        if filename:
            return filename
    return None

xye_wildcard = 'XYE (*.xye)|*.xye|' \
           'XY (*.xy)|*.xy|' \
           'DAT (*.dat)|*.dat|'\
           'RAW (Bruker V3) (*.raw)|*.raw|'\
           'All files (*.*)|*.*'

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
    wildcard =   'txt (*.txt)|*.txt| All files (*.*)|*.*'
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

class SaveProcessedDirSelector(HasTraits):
    file_type=Enum('xye','fxye')('xye')
    path = Directory()

    def __init__(self, default_dir):
        super(SaveProcessedDirSelector,self).__init__()
        self.path = default_dir

    trait_view = View(VGroup(
        Item(name='file_type', editor=EnumEditor(values={
                    'xye'   : '1: XYE',
                    'fxye'   : '2: GSAS fxye',
                    }, cols=1),style='simple'),
        Item(name='path', label='Directory', style='simple')),
        title='Select file type and directory',
        buttons = [OKButton, CancelButton],
        kind='modal',width=0.5, height=0.5,
    )


def get_save_processed_dir(default_dir,wildcard):
    dialog = SaveProcessedDirSelector(default_dir)
    result= dialog.edit_traits()
    return result,dialog.path,dialog.file_type
