from traits.api import Str, HasTraits, Button, Enum, Bool
from traitsui.api import UItem, HGroup, VGroup, Group, View, spring

from processing import rescale
from mpl_plot import MplPlot
from chaco_plot import StackedPlot, Surface2DPlot
from ui_helpers import get_save_as_filename, open_file_with_default_handler


class PlotGenerator(HasTraits):

    plot_types = [
        "Stacked",
        "2D surface",
        "3D plot (slow)",
    ]

    plot_type = Enum(plot_types)
    reset_button = Button("Reset view")
    save_button = Button("Save plot...")
    copy_button = Button("Copy to clipboard")
    scale = Enum('linear', 'log', 'sqrt')
    replot = Bool(False)

    status = Str

    def _on_redraw(self, drawing):
        self.status = 'Rendering plot...' if drawing else 'Done'

    def _set_plots(self, *args):
        plot_list = args
        self.plots = {}
        for i, plot in enumerate(plot_list):
            self.plots[self.plot_types[i]] = plot
            # Traits needs an attribute set on this class to
            # be able to find traits in the plot objects.
            setattr(self, self._plot_attr_name(plot), plot)

    def _plot_attr_name(self, plot):
            return '_plot_' + str(id(plot))

    def __init__(self, *args, **kws):
        self._set_plots(
            StackedPlot(),
            Surface2DPlot(),
            MplPlot(callback_obj=self),
        )
        super(PlotGenerator, self).__init__(*args, **kws)
        self.datasets = kws['datasets']
        self.cached_data = {}
        self._plot_type_changed()

    def __del__(self):
        del self.plots

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
        plot_containers = []
        for plot_type in PlotGenerator.plot_types:
            plot_group = self.plots[plot_type].traits_group(
                self._plot_attr_name(self.plots[plot_type]),
                visible_when="plot_type == '%s'" % plot_type
            )
            plot_containers.append(plot_group)

        view = View(
            VGroup(
                menu_group,
                Group(*plot_containers),
            ),
            title='Plot generator', resizable=True, width=900, height=600,
            statusbar='status',
        )
        self.edit_traits(view=view)

    def _scale_changed(self):
        self.replot = True
        self._plot_type_changed()

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

    def _plot_type_changed(self):
        self._update_status('Generating plot...')
        self.replot = True
        self._generate_plot()
        self._update_status('Done')

    def _generate_plot(self):
        if self.plot_type not in self.cached_data or self.replot:
            x, y, z = self.plots[self.plot_type].prepare_data(self.datasets)
            z = rescale(z, method=self.scale)
            self.cached_data[self.plot_type] = x, y, z
            self.replot = False

        x, y, z = self.cached_data[self.plot_type]
        return self.plots[self.plot_type].plot(x, y, z, scale=self.scale)
