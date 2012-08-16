import os
import re

from enable.api import ComponentEditor
from traits.api import List, Str, Float, HasTraits, Instance, Button, Enum, Bool
from traitsui.api import Item, UItem, HGroup, VGroup, View, spring, Label, CheckListEditor, Tabbed, DefaultOverride
from pyface.api import FileDialog, OK
from chaco.api import OverlayPlotContainer

from xye import XYEDataset
from chaco_output import PlotOutput
from raw_data_plot import RawDataPlot
from fixes import fix_background_color
from dataset_editor import DatasetEditor, DatasetUI
from ui_helpers import get_save_as_filename, open_file_dir_with_default_handler, get_file_list_from_dialog
import processing
from processing import DatasetProcessor
from plot_generator import PlotGenerator

# Linux/Ubuntu themes cause the background of windows to be ugly and dark
# grey. This fixes that.
fix_background_color()


size = (1200, 700)
title = "Sculpd"


def create_datasetui(dataset):
    ui = DatasetUI(name=dataset.name, dataset=dataset, color=None)
    dataset.metadata['ui'] = ui
    return ui


class MainApp(HasTraits):
    container = Instance(OverlayPlotContainer)

    file_paths = List(Str)
    open_files = Button("Open files...")
    edit_datasets = Button("Edit datasets...")
    generate_plot = Button("Generate plot...")
    help_button = Button("Help...")

    scale = Enum('linear', 'log', 'sqrt')
    options = List
    reset_button = Button("Reset view")
    copy_to_clipboard = Button("Copy to clipboard")
    save_as_image = Button("Save as image...")

    load_positions = Button
    merge_method = Enum('none', 'merge', 'splice')('splice')
    merge_regrid = Bool(False)
    normalise = Bool(True)
    correction = Float(0.0)
    align_positions = Bool(False)
    bt_start_peak_select = Button
    bt_end_peak_select = Button
    peak_selecting = Bool(False)

    what_to_plot = Enum('Plot new', 'Plot old and new')('Plot old and new')

    bt_process = Button("Apply")
    bt_undo_processing = Button("Undo")
    bt_save = Button("Save...")

    raw_data_plot = Instance(RawDataPlot)

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
        UItem('load_positions'),
        spring,
        Label('Merge method:'),
        UItem('merge_method', enabled_when='object._has_data()'),
        HGroup(
            VGroup(
                Item('merge_regrid', label='Grid', enabled_when='object._has_data()'),
                Item('normalise', label='Normalise', enabled_when='object._has_data()'),
                show_left=True,
                springy=False,
            ),
            springy=False,
        ),
        spring,
        HGroup(Item('align_positions')),
        HGroup(
            UItem('bt_start_peak_select', label='Select peak',
                  enabled_when='object.align_positions and not object.peak_selecting'),
            UItem('bt_end_peak_select', label='Done',
                  enabled_when='object.peak_selecting'),
        ),
        spring,
        Label('Zero correction:'),
        UItem('correction', enabled_when='object._has_data()'),
        spring,
        UItem('what_to_plot', editor=DefaultOverride(cols=1), style='custom'),
        spring,
        UItem('bt_process', enabled_when='len(object.dataset_pairs) != 0'),
        UItem('bt_undo_processing', enabled_when='object.undo_state is not None'),
        UItem('bt_save', enabled_when='object._has_data()'),
        label='Process',
        springy=False,
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
                    springy=False,
                ),
                show_border=False,
            ),
            UItem('container', editor=ComponentEditor(bgcolor='white')),
            show_border=False,
        ),
        resizable=True, title=title, width=size[0], height=size[1]
    )

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
        range_low, range_high = self.raw_data_plot.end_range_select()
        # fit the peak in all loaded dataseries
        for datapair in self._get_dataset_pairs():
            processing.fit_peaks_for_a_dataset_pair(
                range_low, range_high, datapair, self.normalise)
        self.peak_selecting = False

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
                                     self.merge_method, self.merge_regrid)
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
        self.dataset_pairs = set()
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

    def _add_dataset_pair(self, filename):
        """
        Adds two datasets (one referred to by filename and its partnered position) to the
        self.datasets dictionary and the dataset_pairs set.
        """
        def get_position(filename):
            m = re.search('_p([0-9])_', filename)
            try:
                return int(m.group(1))
            except (AttributeError, ValueError):
                return None

        current_directory, filebase = os.path.split(filename)
        position_index = get_position(filename)
        if position_index is None:
            return

        # get the index of the associated position, e.g. 2=>1, 1=>2, 5=>6, 6=>5 etc.
        other_position_index = ((position_index-1)^1)+1
        # base filename for the associated position.
        other_filebase = re.sub('_p[0-9]_',
                                '_p{}_'.format(str(other_position_index)),
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
        if (position_index&1) == 0:
            self.dataset_pairs.add((other_filebase, filebase))
        else:
            self.dataset_pairs.add((filebase, other_filebase))

    def _file_paths_changed(self, new):
        """
        When the file dialog box is closed with a selection of filenames,
        Generate a list of all the filenames and pair them off with the associated* positions,
        Generate a sorted list of all the pairs,
        Add all the associated datasets to the datasets structure.
        * - Positions are always paired e.g. 1 and 2, or 3 and 4, so a selection with
        either 1 or 2 should generate the pair 1 and 2.
        """
        self.datasets = []
        self.dataset_pairs = set()
        # self.file_paths is modified by _add_dataset_pair() so iterate over a copy of it.
        for filename in self.file_paths[:]:
            self._add_xye_dataset(filename)
        self._plot_datasets()
        self.datasets.sort(key=lambda d: d.name)

    def _load_positions_changed(self):
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
Left drag = Pan the plot
Right drag = Zoom a selection of the plot
Right click = Undo zoom
Esc = Reset zoom/pan
Mousewheel = Zoom in/out
"""


def main():
    demo = MainApp()
    demo.configure_traits()

if __name__ == "__main__":
    main()

