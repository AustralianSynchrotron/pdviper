from enable.api import ComponentEditor
from traits.api import Str, HasTraits, Instance, Button, Enum, Bool
from traitsui.api import Item, UItem, HGroup, VGroup, View, spring
from chaco.api import OverlayPlotContainer

from processing import rescale
from mpl_plot import MplPlot
from chaco_plot import StackedPlot, Surface2DPlot
from ui_helpers import get_save_as_filename, open_file_with_default_handler


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


