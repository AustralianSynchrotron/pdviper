import os
import re
from os.path import basename

from enable.api import ComponentEditor
from traits.api import List, Str, Float, HasTraits, Instance, Button, Enum, Bool, Event
from traitsui.api import Item, UItem, HGroup, VGroup, View, spring, Label, CheckListEditor, ButtonEditor, Tabbed
from pyface.api import FileDialog, OK
from chaco.api import OverlayPlotContainer

from xye import XYEDataset
from chaco_output import PlotOutput
from raw_data_plot import RawDataPlot
from processing import rescale
from mpl_plot import MplPlot
from chaco_plot import StackedPlot, Surface2DPlot
from fixes import fix_background_color
from dataset_editor import DatasetEditor, DatasetUI

import processing

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
    bt_select_peak_event_controller = Event
    bt_select_peak_label = Str("Select peak")
    bt_select_peak = UItem('bt_select_peak_event_controller',
                          editor = ButtonEditor(label_value='bt_select_peak_label'),
                          enabled_when='object._has_data()')
    bt_auto_align_series = Button("Auto align series")
    
    correction = Float(0.0)

    help_button = Button("Help...")
    reset_button = Button("Reset view")
    options = List
    scale = Enum('linear', 'log', 'sqrt')
    merge_method = Enum('none', 'merge', 'splice')('splice')
    merge_regrid = Bool(False)
    normalise = Bool(True)

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
        Label('Align series:'),
        bt_select_peak,
        UItem('bt_auto_align_series', enabled_when='object._has_data()'),
        spring,
        '_',
        spring,
        Label('Correction:'),
        UItem('correction', enabled_when='object._has_data()'),
        spring,
        '_',
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
        label='Process',
        springy=False,
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
#        self.file_paths = [ "0.xye", "1.xye" ]
        self.file_paths = []

    def _open_files_changed(self):
        wildcard = 'XYE (*.xye)|*.xye|' \
                   'All files (*.*)|*.*'
        dlg = FileDialog(title='Choose files', action='open files', wildcard=wildcard)
        if dlg.open() == OK:
            self.file_paths = dlg.paths

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

    def _bt_select_peak_event_controller_fired(self):
        '''
        Button click event handler for peak alignment. Controls enabling and disabling the
        range selection tool and cycling the button label that indicates the bottun mode. 
        '''
        plot = self.raw_data_plot
        # Use the button label to determine the button state
        if self.bt_select_peak_label == 'Select peak':
            plot.add_range_selection_tool()
            # disable zoom tool and change selection cursor to a vertical line
            plot.zoom_tool.drag_button = None
            plot.crosslines[1].visible = False
            self.bt_select_peak_label = 'Align series'
        elif self.bt_select_peak_label == 'Align series':
            # reenable zoom tool and change selection cursor back to crossed lines
            plot.remove_range_selection_tool()
            plot.zoom_tool.drag_button = 'left'
            plot.crosslines[1].visible = True
            self.bt_select_peak_label = 'Select peak'

            range_low, range_high = plot.get_range_selection_tool_limits()

            # fit the peak in all loaded dataseries
            datasets_dict = dict([ (d.name, d) for d in self.datasets ])
            for filename1, filename2 in self.dataset_pairs:
                datapair = datasets_dict[filename1], datasets_dict[filename2]
                processing.fit_peaks_for_a_dataset_pair(range_low, range_high, datapair)

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

    def _plot_datasets(self):
        self.raw_data_plot.plot_datasets(self.datasets, scale=self.scale)
        self._options_changed(self.options)
        self.container.request_redraw()

    def _edit_datasets_changed(self):
        editor = DatasetEditor(datasets=self.datasets)
        editor.edit_traits()
        self._plot_datasets()

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


class PlotGenerator(HasTraits):
    PLOT_STACKED = "Stacked"
    PLOT_3D = "3D surface (slow)"
    PLOT_2D = "2D surface"

    plot_type = Enum(PLOT_STACKED, PLOT_2D, PLOT_3D)
    reset_button = Button("Reset view")
    save_button = Button("Save plot...")
    copy_button = Button("Copy to clipboard")
    plot_container = Instance(OverlayPlotContainer)

    flip_order = Bool(False)
    scale = Enum('linear', 'log', 'sqrt')

    mpl_plot = Instance(MplPlot)

    status = Str

    def _on_redraw(self, drawing):
        self.status = 'Rendering plot...' if drawing else 'Done'

    def __init__(self, *args, **kws):
        super(PlotGenerator, self).__init__(*args, **kws)
        self.plot = None
        self.mpl_plot = MplPlot(callback_obj=self)
        self.plots = {
            PlotGenerator.PLOT_STACKED: StackedPlot(),
            PlotGenerator.PLOT_2D: Surface2DPlot(),
            PlotGenerator.PLOT_3D: self.mpl_plot,
        }
        self.plot_container = OverlayPlotContainer(
            bgcolor='white', use_backbuffer=True)
        self.datasets = kws['datasets']
        self.cached_data = {}
        self._plot_type_changed()

    def __del__(self):
        self.mpl_plot.close()
        del self.plots
        del self.mpl_plot

    def show(self):
        menu_group = HGroup(
                    UItem('plot_type', style='custom'),
                    spring,
                    UItem('scale'),
                    UItem('reset_button'),
                    spring,
                    UItem('save_button'),
                    UItem('copy_button'),
                    spring,
                )

        view = View(
            VGroup(
                menu_group,
                Item('flip_order',
                     visible_when="plot_type == '%s'" % PlotGenerator.PLOT_STACKED),
                UItem('plot_container',
                     editor=ComponentEditor(bgcolor='white'),
                     visible_when="plot_type != '%s'" % PlotGenerator.PLOT_3D
                ),
                self.mpl_plot.traits_group('mpl_plot',
                    visible_when="plot_type == '%s'" % PlotGenerator.PLOT_3D),
            ),
            title='Plot generator', resizable=True, width=900, height=600,
            statusbar='status',
        )
        self.edit_traits(view=view)

    def _flip_order_changed(self):
        self._plot_type_changed()

    def _scale_changed(self):
        self._plot_type_changed(replot=True)

    def _reset_button_changed(self):
        self.plots[self.plot_type].reset_view()

    def _update_status(self, status, delay=0):
        def _update():
            self.status = status
        import wx
        if delay == 0:
            _update()
        else:
            wx.CallLater(delay, _update).Start()

    def _save_button_changed(self):
        filename = get_save_as_filename()
        if filename is None:
            return
        self.plots[self.plot_type].save_as(filename)
        open_file_with_default_handler(filename)

    def _copy_button_changed(self):
        self.plots[self.plot_type].copy_to_clipboard()

    def _plot_type_changed(self, replot=False):
        self._update_status('Generating plot...')
        new_plot = self._generate_plot(replot=replot)
        if new_plot is not None:
            if self.plot:
                self.plot_container.remove(self.plot)
            self.plot = new_plot
            self.plot_container.add(new_plot)
            self.plot_container.request_redraw()
        self._update_status('Done')

    def _generate_plot(self, replot=False):
        if self.plot_type not in self.cached_data or replot:
            x, y, z = self.plots[self.plot_type].prepare_data(self.datasets)
            z = rescale(z, method=self.scale)
            self.cached_data[self.plot_type] = x, y, z

        x, y, z = self.cached_data[self.plot_type]
        if self.plot_type == PlotGenerator.PLOT_STACKED and self.flip_order:
            z = z[::-1,:]
        return self.plots[self.plot_type].plot(x, y, z, scale=self.scale)


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


def get_save_as_filename():
    wildcard =  'PNG file (.png)|*.png|TIFF file (.tiff)|*.tiff|EPS file (.eps)|*.eps|SVG file (.svg)|*.svg|'
    dialog = FileDialog(action='save as', title='Save as', wildcard=wildcard)
    if dialog.open() == OK:
        filename = dialog.path
        if filename:
            return filename
    return None


def open_file_with_default_handler(filename):
    try:
        import webbrowser
        webbrowser.open_new_tab(filename)
    except:
        pass



def main():
    demo = MainApp()
    demo.configure_traits()

if __name__ == "__main__":
    main()

