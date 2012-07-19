from os.path import basename

from enable.api import ComponentEditor
from traits.api import List, Str, HasTraits, Instance, Button, Enum, Bool
from traitsui.api import Item, UItem, HGroup, VGroup, View, NullEditor, spring, Label, CheckListEditor
from pyface.api import FileDialog, OK
from chaco.api import OverlayPlotContainer

from xye import XYEDataset
from chaco_output import PlotOutput
from raw_data_plot import RawDataPlot
from processing import rescale
from mpl_plot import MplPlot
from chaco_plot import StackedPlot, Surface2DPlot
from fixes import fix_background_color

# Linux/Ubuntu themes cause the background of windows to be ugly and dark
# grey. This fixes that.
fix_background_color()

size = (1200, 700)
title = "Sculpd"


class MainApp(HasTraits):
    container = Instance(OverlayPlotContainer)

    file_paths = List(Str)
    open_files = Button("Open files...")
    copy_to_clipboard = Button("Copy to clipboard")
    save_as_image = Button("Save as image...")
    generate_plot = Button("Generate plot...")
    help_button = Button("Help...")
    options = List
    scale = Enum('linear', 'log', 'sqrt')

    raw_data_plot = Instance(RawDataPlot)

    traits_view = View(
        HGroup(
            VGroup(
                UItem('open_files'),
                UItem('help_button'),
                UItem('generate_plot', enabled_when='object._has_data()'),
                spring,
                '_',
                spring,
                Label('Scale:', enabled_when='object._has_data()'),
                UItem('scale', enabled_when='object._has_data()'),
                UItem('options', editor=CheckListEditor(name='_options'), style='custom', enabled_when='object._has_data()'),
                spring,
                '_',
                spring,
                UItem('copy_to_clipboard', enabled_when='object._has_data()'),
                UItem('save_as_image', enabled_when='object._has_data()'),
                show_border=False
            ),
            VGroup(
                UItem(editor=NullEditor()),
                show_border=False,
            ),
            UItem('container', editor=ComponentEditor()),
            show_border=False
        ),
        resizable=True, title=title, width=size[0], height=size[1]
    )

    def _has_data(self):
        return len(self.datasets) != 0

    def __init__(self, *args, **kws):
        super(MainApp, self).__init__(*args, **kws)
        self.datasets = {}
        self.raw_data_plot = RawDataPlot(self.datasets)
        self.plot = self.raw_data_plot.get_plot()
        self.container = OverlayPlotContainer(self.plot,
            padding_left=50, fill_padding=True,
            bgcolor="white", use_backbuffer=True)
        self.pan_tool = None
        # The list of all options.
        self._options = [ 'Show legend', 'Show gridlines' ]
        # The list of currently set options, updated by the UI.
        self.options = self._options
        self.file_paths = [ "0.xye", "1.xye" ]

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
        self.container.request_redraw()

    def _save_as_image_changed(self):
        if len(self.datasets) == 0:
            return
        filename = get_save_as_filename()
        if filename:
            PlotOutput.save_as_image(self.container, filename, change_bounds=False)
            open_file_with_default_handler(filename)

    def _copy_to_clipboard_changed(self):
        if self.datasets:
            PlotOutput.copy_to_clipboard(self.container)

    def _scale_changed(self):
        self._plot_datasets()

    def _file_paths_changed(self):
        self.datasets = {}
        for filename in self.file_paths:
            self._add_xye_dataset(filename)
        self._plot_datasets()

    def _plot_datasets(self):
        self.raw_data_plot.plot_datasets(self.datasets, scale=self.scale)
        self._options_changed(self.options)
        self.container.request_redraw()

    def _generate_plot_changed(self):
        if self.datasets:
            generator = PlotGenerator(datasets=self.datasets)
            generator.show()

    def _help_button_changed(self):
        help_box = HelpBox()
        help_box.edit_traits()

    def _add_xye_dataset(self, file_path):
        try:
            dataset = XYEDataset.from_file(file_path)
        except IOError:
            return
        filename = basename(file_path)
        self.datasets[filename] = dataset


class PlotGenerator(HasTraits):
    PLOT_STACKED = "Stacked"
    PLOT_3D = "3D surface (slow)"
    PLOT_2D = "2D surface"

    plot_type = Enum(PLOT_STACKED, PLOT_2D, PLOT_3D)
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
            bgcolor='white', use_backbuffer=True,
            padding_left=30, fill_padding=True)
        self.datasets = kws['datasets']
        self.cached_data = {}
        self._plot_type_changed()

    def __del__(self):
        self.mpl_plot.close()
        del self.plots
        del self.mpl_plot

    def show(self):
        menu_group = HGroup(
                    UItem('plot_type', style='custom'),#, padding=5),
                    spring,
                    UItem('scale'),
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
                     editor=ComponentEditor(),
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
        self.help_text = open('help_text.txt').read()


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



demo = MainApp()

if __name__ == "__main__":
    demo.configure_traits()

