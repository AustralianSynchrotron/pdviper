import logger
import os
import re

from enable.api import ComponentEditor
from traits.api import List, Str, Float, HasTraits, Instance, Button, Enum, Bool, \
                        DelegatesTo, Range
from traitsui.api import Item, UItem, HGroup, VGroup, View, spring, Label, \
                        CheckListEditor, Tabbed, DefaultOverride, EnumEditor
from pyface.api import FileDialog, OK
from chaco.api import OverlayPlotContainer

from xye import XYEDataset
from chaco_output import PlotOutput
from raw_data_plot import RawDataPlot
from fixes import fix_background_color
from dataset_editor import DatasetEditor, DatasetUI
from wavelength_editor import WavelengthEditor, WavelengthUI
from ui_helpers import get_save_as_filename, open_file_dir_with_default_handler, get_file_list_from_dialog
import processing
from processing import DatasetProcessor
from plot_generator import PlotGenerator
from peak_fit_window import PeakFitWindow


# Linux/Ubuntu themes cause the background of windows to be ugly and dark
# grey. This fixes that.
fix_background_color()


size = (1200, 700)
title = "Sculpd"


def create_datasetui(dataset):
    ui = DatasetUI(name=dataset.name, dataset=dataset, color=None)
    dataset.metadata['ui'] = ui
    ui_w = WavelengthUI(name=dataset.name, dataset=dataset)
    dataset.metadata['ui_w'] = ui_w
    return (ui, ui_w)
    return ui

class Global(HasTraits):
    """
    This is just a container class for the file list so that the normalisation reference
    selector can use a drop-down list selector normally reserved by traitsui for Enum
    traits, but where we want to use a list instead and have the dropdown updated upon
    updates to the list. See discussion here describing this:
    http://enthought-dev.117412.n3.nabble.com/How-to-force-an-update-to-an-enum-list-to-propagate-td3489135.html
    """
    file_list = List([])

    def populate_list(self, filepaths):
        positions = set()
        for f in filepaths:
            positions.add(re.search('_(p[1-4])_', os.path.basename(f)).group(1))
        self.file_list = sorted(positions) + [os.path.basename(f) for f in filepaths]

g = Global()

class MainApp(HasTraits):
    container = Instance(OverlayPlotContainer)

    file_paths = List(Str)
    # Button group above tabbed area
    open_files = Button("Open files...")
    edit_datasets = Button("Edit datasets...")
    generate_plot = Button("Generate plot...")
    help_button = Button("Help...")

    # View tab
    scale = Enum('linear', 'log', 'sqrt')
    options = List
    reset_button = Button("Reset view")
    copy_to_clipboard = Button("Copy to clipboard")
    save_as_image = Button("Save as image...")

    # Process tab
    merge_positions = Enum('all', 'p1+p2', 'p3+p4', 'p12+p34')('p1+p2')
    load_partners = Button
    splice = Bool(True)
    merge = Bool(False)
    merge_regrid = Bool(False)
    normalise = Bool(True)
    # See comment in class Global() for an explanation of the following traits
    g = Instance(Global, ())
    file_list = DelegatesTo('g')
    normalisation_source_filenames = Enum(values='file_list')
    def _g_default(self):
        return g

    correction = Float(0.0)
    align_positions = Bool(False)
    bt_start_peak_select = Button
    bt_end_peak_select = Button
    peak_selecting = Bool(False)

    what_to_plot = Enum('Plot new', 'Plot old and new')('Plot old and new')

    bt_process = Button("Apply")
    bt_undo_processing = Button("Undo")
    bt_save = Button("Save...")

    # Background removal tab
    bt_manually_define_background = Button("Define")
    polynomial_order = Range(1, 20)(7)
    bt_poly_fit = Button("Poly fit")
    bt_load_background = Button("Load...")

    # theta/d/Q tab
    filename_field = Str("d")
    bt_convertscale_abscissa = Button("Convert/scale abscissa...")

    raw_data_plot = Instance(RawDataPlot)

    #-------------------------------------------------------------------------------------
    # MVC View
    view_group = VGroup(
        Label('Scale:'),
        UItem('scale', enabled_when='object._has_data()'),
        UItem('options', editor=CheckListEditor(name='_options'), style='custom', enabled_when='object._has_data()'),
        UItem('reset_button', enabled_when='object._has_data()'),
        spring,
        '_',
        spring,
        UItem('copy_to_clipboard', enabled_when='object._has_data()'),
        UItem('save_as_image', enabled_when='object._has_data()'),
        label='View',
        springy=False,
    )

    process_group = VGroup(
        VGroup(
            Label('Positions to process:'),
            UItem(name='merge_positions',
                 style='custom',
                 editor=EnumEditor(values={
                     'p1+p2'   : '1: p1+p2',
                     'p3+p4'   : '2: p3+p4',
                     'p12+p34' : '3: p12+p34',
                     'all'    : '4: all',
                 }, cols=2),
                 enabled_when='object._has_data()'
            ),
            UItem('load_partners', enabled_when='object._has_data() and object.merge_positions is not "all"'),
            show_border = True,
        ),
        VGroup(
            HGroup(Item('align_positions'), enabled_when='object._has_data() and object.merge_positions is not "all"'),
            HGroup(
                UItem('bt_start_peak_select', label='Select peak',
                      enabled_when='object.align_positions and not object.peak_selecting and object.merge_positions is not "all"'),
                UItem('bt_end_peak_select', label='Align',
                      enabled_when='object.peak_selecting and object.merge_positions is not "all"'),
            ),
            Item('correction', label='Zero correction:', enabled_when='object._has_data()'),
            show_border = True,
        ),
        VGroup(
            HGroup(Item('splice'), Item('merge'), enabled_when='object._has_data()'),
            HGroup(
                Item('normalise', label='Normalise', enabled_when='object._has_data()'),
                Item('merge_regrid', label='Grid', enabled_when='object._has_data()'),
            ),
            VGroup(
                Label('Normalise to:'),
                UItem('normalisation_source_filenames', style='simple',
                     enabled_when='object.normalise and object._has_data()'),
            ),
            show_border = True,
        ),
        spring,
        UItem('what_to_plot', editor=DefaultOverride(cols=2), style='custom',
              enabled_when='object._has_data()'),
        spring,
#        UItem('bt_process', enabled_when='len(object.dataset_pairs) != 0'),
        UItem('bt_process', enabled_when='object._has_data()'),
        UItem('bt_undo_processing', enabled_when='object.undo_state is not None'),
        UItem('bt_save', enabled_when='object._has_data()'),
        label='Process',
        springy=False,
    )

    background_removal_group =  VGroup(
        VGroup(
            Label('Manually define:'),
            UItem('bt_manually_define_background', enabled_when='object._has_data()'),
            show_border = True,
        ),
        VGroup(
            Label('Fit polynomial:'),
            HGroup(
                   Item('polynomial_order', label='order', enabled_when='object._has_data()'),
            ),
            UItem('bt_poly_fit', enabled_when='object._has_data()'),
            show_border = True,
        ),
        VGroup(
            Label('Load from file:'),
            UItem('bt_load_background', enabled_when='object._has_data()'),
            show_border = True,
        ),
        label='Backgrnd',
        springy=False,
    )

    convert_xscale_group = VGroup(
        Label('Filename label (prefix_<label>_nnnn.xye):'),
        UItem('filename_field',
             enabled_when='object._has_data()'),
        UItem('bt_convertscale_abscissa',
              label='Convert/scale abscissa...',
              enabled_when='object._has_data()',
        ),
    label=ur'\u0398 d Q',
    springy=True,
    )

    traits_view = View(
        HGroup(
            VGroup(
                UItem('open_files'),
                UItem('edit_datasets', enabled_when='object._has_data()'),
                UItem('generate_plot', enabled_when='object._has_data()'),
                UItem('help_button'),
                spring,
                spring,
                Tabbed(
                    view_group,
                    process_group,
                    background_removal_group,
                    convert_xscale_group,
                    springy=False,
                ),
                show_border=False,
            ),
            UItem('container', editor=ComponentEditor(bgcolor='white')),
            show_border=False,
        ),
        resizable=True, title=title, width=size[0], height=size[1]
    )

    #-------------------------------------------------------------------------------------
    # MVC Control

    def _has_data(self):
        return len(self.datasets) != 0

    def __init__(self, *args, **kws):
        """
        self.datasets = [ <XYEDataset>, ..., <XYEDataset> ]
        self.dataset_pairs = set([ (<XYEDataset-p1>, <XYEDataset-p2>),
                                   ...,
                                   (<XYEDataset-p1>, <XYEDataset-p2>) ])
        """
        super(MainApp, self).__init__(*args, **kws)
        self.datasets = []
        self.dataset_pairs = set()
        self.undo_state = None
        self.raw_data_plot = RawDataPlot()
        self.plot = self.raw_data_plot.get_plot()
        self.container = OverlayPlotContainer(self.plot,
            bgcolor="white", use_backbuffer=True,
            border_visible=False)
        self.pan_tool = None
        # The list of all options.
        self._options = [ 'Show legend', 'Show gridlines', 'Show crosslines' ]
        # The list of currently set options, updated by the UI.
        self.options = self._options
        self.file_paths = []

    def _open_files_changed(self):
        file_list = get_file_list_from_dialog()
        if file_list:
            self.file_paths = file_list

    def _options_changed(self, opts):
        # opts just contains the keys that are true.
        # Create a dict all_options that has True/False for each item.
        all_options = dict.fromkeys(self._options, False)
        true_options = dict.fromkeys(opts, True)
        all_options.update(true_options)
        self.raw_data_plot.show_legend(all_options['Show legend'])
        self.raw_data_plot.show_grids(all_options['Show gridlines'])
        self.raw_data_plot.show_crosslines(all_options['Show crosslines'])
        self.container.request_redraw()

    def _bt_start_peak_select_changed(self):
        self.raw_data_plot.start_range_select()
        self.peak_selecting = True

    def _bt_end_peak_select_changed(self):
        self.peak_selecting = False
        selection_range = self.raw_data_plot.end_range_select()
        if not selection_range:
            return

        range_low, range_high = selection_range
        # fit the peak in all loaded dataseries
        self._get_partners()
        for datapair in self._get_dataset_pairs():
            processing.fit_peaks_for_a_dataset_pair(
                range_low, range_high, datapair, self.normalise)
        editor = PeakFitWindow(dataset_pairs=self._get_dataset_pairs(),
                               range=selection_range)
        editor.edit_traits()

    def _get_dataset_pairs(self):
        datasets_dict = dict([ (d.name, d) for d in self.datasets ])
        return [ (datasets_dict[file1], datasets_dict[file2]) \
                    for file1, file2 in self.dataset_pairs ]

    def _bt_process_changed(self):
        '''
        Button click event handler for processing. 
        '''
        # Save the unprocessed data series at this point for later undoing
        processed_datasets = []
        processor = DatasetProcessor(self.normalise, self.correction,
                                     self.align_positions,
                                     self.splice, self.merge, self.merge_regrid,
                                     self.normalisation_source_filenames,
                                     self.datasets)
        # Processing at this point depends on the "Positions to process:" radiobutton
        # selection:
        # If Splice==True, get all pairs and splice them
        # If Merge==True, get all pairs and merge them
        # If Normalise==True, always normalise
        # If Grid===True, output gridded and ungridded
        # The following processing code sould really be placed into a processor.process()
        # method, but I only worked out how to pass required stuff late in the day, so
        # I do this stuff here.
        if self.merge_positions == 'all':
            # Handle "all" selection for regrid and normalise
            for d in self.datasets:
                dataset = processor.normalise_me(d)
                if dataset is not None:
                    processed_datasets.extend(dataset)
                    dataset.metadata['ui'].name = dataset.name + ' (processed)'
                    dataset.metadata['ui'].color = None

                dataset = processor.regrid_me(d)
                processed_datasets.extend(dataset)
                dataset.metadata['ui'].name = dataset.name + ' (processed)'
                dataset.metadata['ui'].color = None
        else:
            self._get_partners()        # pair up datasets corresponding to the radiobutton selection
            for dataset_pair in self._get_dataset_pairs():
                datasets = processor.process_dataset_pair(dataset_pair)
                for dataset in datasets:
                    dataset.metadata['ui'].name = dataset.name + ' (processed)'
                    dataset.metadata['ui'].color = None
                processed_datasets.extend(datasets)

        self.processed_datasets = processed_datasets
        self._plot_processed_datasets()

    def _plot_processed_datasets(self):
        self._save_state()
        self.dataset_pairs = set()          # TODO: Check whether this line should be removed
        if 'old' not in self.what_to_plot:
            self.datasets = []
        if 'new' in self.what_to_plot:
            self.datasets.extend(self.processed_datasets)
        self._plot_datasets()

    def _save_state(self):
        self.undo_state = (self.datasets[:], self.dataset_pairs.copy())

    def _restore_state(self):
        if self.undo_state is not None:
            self.datasets, self.dataset_pairs = self.undo_state
            self.undo_state = None

    def _bt_undo_processing_changed(self):
        self._restore_state()
        self._plot_datasets()

    def _bt_save_changed(self):
        wildcard = 'All files (*.*)|*.*'
        default_filename = 'prefix'
        dlg = FileDialog(title='Save results', action='save as',
                         default_filename=default_filename, wildcard=wildcard)
        if dlg.open() == OK:
            for dataset in self.processed_datasets:
                filename = os.path.join(dlg.directory, dlg.filename + '_'  + dataset.name)
                dataset.save(filename)
            open_file_dir_with_default_handler(dlg.path)

    def _save_as_image_changed(self):
        if len(self.datasets) == 0:
            return
        filename = get_save_as_filename()
        if filename:
            PlotOutput.save_as_image(self.container, filename)
            open_file_dir_with_default_handler(filename)

    def _copy_to_clipboard_changed(self):
        if self.datasets:
            PlotOutput.copy_to_clipboard(self.container)

    def _scale_changed(self):
        self._plot_datasets()

    def _get_partner(self, position_index):
        # return index of partner; i.e., 2=>1, 1=>2, 3=>4, 4=>3, 12=>34, 34=>12
        if position_index in [1,2,3,4]:
            partner = ((position_index-1)^1)+1
        elif position_index==12:
            partner = 34
        elif position_index==34:
            partner = 12
        else:
            raise 'unparsable position'
        return partner

    def _get_position(self, filename):
        m = re.search('_p([0-9]*)_', filename)
        try:
            return int(m.group(1))
        except (AttributeError, ValueError):
            return None

    def _add_dataset_pair(self, filename):
        current_directory, filebase = os.path.split(filename)
        position_index = self._get_position(filename)
        if position_index is None:
            return

        # base filename for the associated position.
        other_filebase = re.sub('_p{}_'.format(position_index),
                                '_p{}_'.format(self._get_partner(position_index)),
                                filebase)
        other_filename = os.path.join(current_directory, other_filebase)
        if not os.path.exists(other_filename):
            return

        # OK, we've got the names and paths, now add the actual data and references.
        if other_filename not in self.file_paths:
            self._add_xye_dataset(other_filename)
            # We also need to append the new path to the file_paths List trait which is
            # already populated by the files selected using the file selection dialog
            self.file_paths.append(other_filename)
        self._refresh_normalise_to_list()

    def _get_partners(self):
        """
        Populates the self.dataset_pairs list with all dataset partners in
        self.file_paths corresponding to the merge_positions radiobutton selection.
        """
        matching_re = {'all':    ''            ,
                       'p1+p2':  '_p[12]_'     ,
                       'p3+p4':  '_p[34]_'     ,
                       'p12+p34':'_p(?:12|34)_',
                      }
        basenames = [os.path.basename(f) for f in self.file_paths]
        filtered_paths = [f for f in basenames if re.search(matching_re[self.merge_positions], f) is not None]
        self.dataset_pairs = set()
        for filebase in filtered_paths:
            # base filename for the first position.
            position_index = self._get_position(filebase)
            if position_index is None:
                return
            other_filebase = re.sub('_p{}_'.format(position_index),
                                    '_p{}_'.format(self._get_partner(position_index)),
                                    filebase)
            if filebase in basenames and other_filebase in basenames:
                if position_index == 34 or (position_index&1)==0:
                    self.dataset_pairs.add((other_filebase, filebase))
                else:
                    self.dataset_pairs.add((filebase, other_filebase))
        return self.dataset_pairs

    def _refresh_normalise_to_list(self):
        g.populate_list(self.file_paths)

    def _file_paths_changed(self, new):
        """
        When the file dialog box is closed with a selection of filenames,
        just generate a list of all the filenames
        """
        self.datasets = []
        # self.file_paths is modified by _add_dataset_pair() so iterate over a copy of it.
        for filename in self.file_paths[:]:
            self._add_xye_dataset(filename)
        self._plot_datasets()
        self.datasets.sort(key=lambda d: d.name)
        self._refresh_normalise_to_list()

    def _load_partners_changed(self):
        for filename in self.file_paths[:]:
            self._add_dataset_pair(filename)
        self._plot_datasets()
        self.datasets.sort(key=lambda d: d.name)

    def _plot_datasets(self, reset_view=True):
        self.raw_data_plot.plot_datasets(self.datasets, scale=self.scale,
                                         reset_view=reset_view)
        self._options_changed(self.options)
        self.container.request_redraw()

    def _edit_datasets_changed(self):
        editor = DatasetEditor(datasets=self.datasets)
        editor.edit_traits()
        self._plot_datasets(reset_view=False)

    def _generate_plot_changed(self):
        if self.datasets:
            generator = PlotGenerator(datasets=self.datasets)
            generator.show()

    def _help_button_changed(self):
        help_box = HelpBox()
        help_box.edit_traits()

    def _reset_button_changed(self):
        self.raw_data_plot.reset_view()

    def _add_xye_dataset(self, file_path):
        try:
            dataset = XYEDataset.from_file(file_path)
        except IOError:
            return
        self.datasets.append(dataset)
        create_datasetui(dataset)

    def _bt_convertscale_abscissa_changed(self):
        editor = WavelengthEditor(datasets=self.datasets, filename_field=self.filename_field)
        editor.edit_traits()
        self._plot_datasets(reset_view=False)


class HelpBox(HasTraits):
    help_text = Str

    traits_view = View(
        UItem('help_text', style='readonly', padding=15),
        title='Help',
    )

    def __init__(self, *args, **kws):
        super(HelpBox, self).__init__(*args, **kws)
        self.help_text = \
"""
Left drag = Zoom a selection of the plot
Right drag = Pan the plot
Right click = Undo zoom
Esc = Reset zoom/pan
Mousewheel = Zoom in/out
"""


def main():
    demo = MainApp()
    demo.configure_traits()

if __name__ == "__main__":
    main()

