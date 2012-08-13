import os
import re

from enable.api import ComponentEditor
from traits.api import List, Str, Float, HasTraits, Instance, Button, Enum, Bool
from traitsui.api import Item, UItem, HGroup, VGroup, View, spring, Label, CheckListEditor, Tabbed
from pyface.api import FileDialog, OK
from chaco.api import OverlayPlotContainer

from xye import XYEDataset
from chaco_output import PlotOutput
from raw_data_plot import RawDataPlot
from fixes import fix_background_color
from dataset_editor import DatasetEditor, DatasetUI
from copy import deepcopy
from ui_helpers import get_save_as_filename, open_file_with_default_handler, get_file_list_from_dialog
import processing
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
    copy_to_clipboard = Button("Copy to clipboard")
    save_as_image = Button("Save as image...")
    generate_plot = Button("Generate plot...")

    # To update the button label based on a state machine state, do this:
    # http://osdir.com/ml/python.enthought.devel/2006-10/msg00144.html
    bt_start_peak_select = Button
    bt_end_peak_select = Button
    bt_select_peak_label = Str("Select peak")
    bt_process = Button("Apply")
    bt_undo_processing = Button("Undo")
    bt_save = Button("Save...")

    correction = Float(0.0)

    help_button = Button("Help...")
    reset_button = Button("Reset view")
    options = List
    scale = Enum('linear', 'log', 'sqrt')
    merge_method = Enum('none', 'merge', 'splice')('splice')
    merge_regrid = Bool(False)
    normalise = Bool(True)
    align_positions = Bool(False)
    peak_selecting = Bool(False)

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
        '_',
        spring,
        UItem('bt_process', enabled_when='len(object.dataset_pairs) != 0'),
        UItem('bt_undo_processing', enabled_when='object.undo_state is not None'),
        UItem('bt_save', enabled_when='object._has_data()'),
        label='Process',
        springy=False,
        enabled_when='object._has_data()',
    )

    traits_view = View(
        HGroup(
            VGroup(
                UItem('open_files'),
                UItem('edit_datasets'),
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
        <datasets> is a dictionary whose entries are XYEDataset objects with keys equal to
        the filename of the dataset, e.g. {'BZA-scan_p2_0027.xye', <XYEDataset>}
        <dataset_pairs> is a set containing the keys of (odd,even) pairs of datasets to
        process, e.g. set([('BZA-scan_p1_0025.xye', 'BZA-scan_p2_0025.xye'),
                           ('BZA-scan_p1_0026.xye', 'BZA-scan_p2_0026.xye')])
        """
        super(MainApp, self).__init__(*args, **kws)
        self.datasets = []
        self.dataset_pairs = set()
        self.undo_state = None
        self.raw_data_plot = RawDataPlot(self.datasets)
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
            processing.fit_peaks_for_a_dataset_pair(range_low, range_high, datapair, self.normalise)
        self.peak_selecting = False

    def _get_dataset_pairs(self):
        datasets_dict = dict([ (d.name, d) for d in self.datasets ])
        return [ (datasets_dict[file1], datasets_dict[file2]) for file1, file2 in self.dataset_pairs ]

    def _bt_process_changed(self):
        '''
        Button click event handler for processing. 
        '''
        # Save the unprocessed data series at this point for later undoing
        merged_datasets = []
        for dataset_pair in self._get_dataset_pairs():
            dataset1, dataset2 = dataset_pair
            data1 = dataset1.data
            data2 = dataset2.data

            # normalise
            if self.normalise:
                data2 = processing.normalise_dataset(self.datasets, dataset_pair)

            # trim data from gap edges prior to merging
            data1 = processing.clean_gaps(data1)
            data2 = processing.clean_gaps(data2)

            # zero correct i.e. shift x values
            if self.correction != 0.0:
                data1[:,0] += self.correction
                data2[:,0] += self.correction

            if self.align_positions:
                if 'peak_fit' in dataset1.metadata and \
                   'peak_fit' in dataset2.metadata:
                    x_offset = dataset1.metadata['peak_fit'] - \
                                dataset2.metadata['peak_fit']
                    data2[:,0] += x_offset

            # merge or splice
            if self.merge_method=='merge':
                merged_data = processing.combine_by_merge(data1, data2) 
            elif self.merge_method=='splice':
                merged_data = processing.combine_by_splice(data1, data2) 
            elif self.merge_method=='none':
                raise Exception('TODO:')

            # regrid
            if self.merge_regrid:
                merged_data = processing.regrid_data(merged_data)

            # add merged dataset to our collection
            current_directory, _, parts = self._get_file_path_parts(dataset1.source)
            merged_data_filebase = u'{}{}_{}.{}'.format(parts[1], parts[3], parts[4], parts[5])
            merged_data_filename = os.path.join(current_directory, merged_data_filebase)
            merged_dataset = XYEDataset(merged_data, merged_data_filebase,
                                              merged_data_filename,
                                              deepcopy(dataset1.metadata))
            merged_datasets.append(merged_dataset)
            merged_dataset.metadata['ui'].name = merged_data_filebase
        self._save_state()
        self.datasets = merged_datasets
        self.dataset_pairs = set()
        self._plot_datasets()

    def _save_state(self):
        self.undo_state = (self.datasets, self.dataset_pairs)

    def _restore_state(self):
        if self.undo_state is not None:
            self.datasets, self.dataset_pairs = self.undo_state
            self.undo_state = None

    def _bt_undo_processing_changed(self):
        self._restore_state()
        self._plot_datasets()

    def _bt_save_changed(self):
        wildcard = 'All files (*.*)|*.*'
        _, _, parts = self._get_general_file_path_parts(self.datasets[0].source)
        default_filename = 'prefix'
        dlg = FileDialog(title='Save results', action='save as', default_filename=default_filename, wildcard=wildcard)
        if dlg.open() == OK:
            filename_prefix = dlg.path
            for dataset in self.datasets:
                current_directory, filename, parts = self._get_general_file_path_parts(dataset.source)
                filename = os.path.join(current_directory, '{}_{}_{}.xye'.format(filename_prefix, parts[1], parts[2]))
                dataset.save(filename)

    def _bt_auto_align_series_changed(self):
        # attempt auto alignment
        print 'Auto align series'

    def _save_as_image_changed(self):
        if len(self.datasets) == 0:
            return
        filename = get_save_as_filename()
        if filename:
            PlotOutput.save_as_image(self.container, filename)
            open_file_with_default_handler(filename)

    def _copy_to_clipboard_changed(self):
        if self.datasets:
            PlotOutput.copy_to_clipboard(self.container)

    def _scale_changed(self):
        self._plot_datasets()

    def _get_file_path_parts(self, filename):
        """
        A helper function that parses a filename and returns the filename split into
        useful parts as follows:
        Example filenames:
            path/si640c_low_temp_cal_p1_scan0.000000_adv0_0000.xye
            path/BZA-scan_p2_0026.xye
        The filename path/foo_p1_bar_0123.xye returns the tuple
        ('path', 'foo_p1_bar_0123.xye', ['', 'foo', '1', '_bar', '0123', 'xye', ''])
        The filename path/foo_p1_0123.xye returns the tuple
        ('path', 'foo_p1_0123.xye',
            ['', 'foo', '1', '', '0123', 'xye', ''])
        """
        current_directory, filename = os.path.split(filename)
        # root, ext = os.path.splitext(filename)
        parts = re.split(r'(.+)_p(\d+)(.*)_(\d+)\.(.+)', filename)
        return current_directory, filename, parts

    def _get_general_file_path_parts(self, filename):
        """
        A helper function that parses a filename and returns the filename split into
        useful parts as follows:
        Example filenames:
            path/foo_0000.xye
        The filename path/foo_0123.xye returns the tuple
        ('path', 'foo_0000.xye', ['', 'foo', '0123', 'xye', ''])
        """
        current_directory, filename = os.path.split(filename)
        # root, ext = os.path.splitext(filename)
        parts = re.split(r'(.+)_(\d+)\.(.+)', filename)
        return current_directory, filename, parts

    def _add_dataset_pair(self, filename):
        """
        Adds two datasets (one referred to by filename and its partnered position) to the
        self.datasets dictionary and the dataset_pairs set.
        """
        current_directory, filebase, parts = self._get_file_path_parts(filename)
        position_index = int(parts[2])      # e.g. equals 1 when the filename contains _p1_
        # get the index of the associated position, e.g. 2=>1, 1=>2, 5=>6, 6=>5 etc.
        other_position_index = ((position_index-1)^1)+1
        # base filename for the associated position.
        other_filebase = u'{}_p{}{}_{}.{}'.format(parts[1], str(other_position_index),
                                                  parts[3], parts[4], parts[5])
        other_filename = os.path.join(current_directory, other_filebase)
        # OK, we've got the names and paths, now add the actual data and references.
        self._add_xye_dataset(filename)
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

