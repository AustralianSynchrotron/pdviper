import numpy as np
from numpy import array

from enable.api import Component, ComponentEditor
from traits.api import Instance, Range, Bool, on_trait_change
from traitsui.api import Group, UItem, VGroup, Item, HGroup
from chaco.api import Plot, ArrayPlotData, jet, ColorBar, LinearMapper, HPlotContainer, PlotAxis, PlotLabel, OverlayPlotContainer, LinePlot
from chaco.tools.api import TraitsTool
from chaco.default_colormaps import fix

from chaco_output import PlotOutput
from tools import ClickUndoZoomTool, PanToolWithHistory
from processing import stack_datasets, interpolate_datasets, bin_data, cubic_interpolate
from base_plot import BasePlot
from labels import get_value_scale_label
import settings
from traits_extensions import HasTraitsGroup


class ClickableLinePlot(LinePlot):
    def is_in(self, x, y, threshold=2.):
        screen_pt = x, y
        data_x = self.map_data(screen_pt)
        xmin, xmax = self.index.get_bounds()
        if xmin <= data_x <= xmax:
            if self.orientation == "h":
                sy = screen_pt[1]
            else:
                sy = screen_pt[0]

            interp_y = self.interpolate(data_x)
            interp_y = self.value_mapper.map_screen(interp_y)

            if abs(sy - interp_y) <= threshold:
                return True
        return False


class ChacoPlot(BasePlot, HasTraitsGroup):
    component = Instance(Component)

    def redraw(self):
        self.component.request_redraw()

    def copy_to_clipboard(self):
        PlotOutput.copy_to_clipboard(self.component)

    def save_as(self, filename):
        PlotOutput.save_as_image(self.component, filename)

    def _get_traits_group(self):
        return Group(UItem('component', editor=ComponentEditor()))


class StackedPlot(ChacoPlot):
    offset = Range(0.0, 1.0, 0.015)
    value_range = Range(0.01, 1.05, 1.00)
    flip_order = Bool(False)

    def _get_traits_group(self):
        return VGroup(
                   HGroup(
                       Item('flip_order'),
                       Item('offset'),
                       Item('value_range'),
                   ),
                   UItem('component', editor=ComponentEditor()),
               )

    def __init__(self):
        super(StackedPlot, self).__init__()
        self.container = OverlayPlotContainer(bgcolor='white',
                                         use_backbuffer=True,
                                         border_visible=True,
                                         padding=50,
                                         padding_left=110,
                                         fill_padding=True
                                             )
        self.data = ArrayPlotData()
        self.chaco_plot = None
        self.value_mapper = None
        self.index_mapper = None
        self.x_axis = PlotAxis(component=self.container,
                          orientation='bottom',
                          title=u'Angle (2\u0398)',
                          title_font=settings.axis_title_font,
                          tick_label_font=settings.tick_font)
        y_axis_title = 'Normalized intensity (%s)' % get_value_scale_label('linear')
        self.y_axis = PlotAxis(component=self.container,
                          orientation='left',
                          title=y_axis_title,
                          title_font=settings.axis_title_font,
                          tick_label_font=settings.tick_font)
        self.container.overlays.extend([self.x_axis, self.y_axis])
        self.container.tools.append(
            TraitsTool(self.container, classes=[LinePlot,PlotAxis]))
        self.colors = []
        self.last_flip_order = self.flip_order

    @on_trait_change('offset, value_range, flip_order')
    def _replot_data(self):
        self._plot(self.data_x, None, self.data_z, self.scale)
        self.container.request_redraw()

    def _prepare_data(self, datasets):
        interpolate = True
        stack = stack_datasets(datasets)
        if interpolate:
            (x, z) = interpolate_datasets(stack, points=4800)
            x = array([x] * len(datasets))
        else:
            x, z = map(np.transpose, np.transpose(stack))
        return x, None, z

    def _plot(self, x, y, z, scale):
        self.data_x, self.data_z, self.scale = x, z, scale
        if self.container.components:
            self.colors = map(lambda plot: plot.color, self.container.components)
            if self.last_flip_order != self.flip_order:
                self.colors.reverse()
            self.container.remove(*self.container.components)
        # Use a custom renderer so plot lines are clickable
        self.chaco_plot = Plot(self.data,
                               renderer_map={ 'line': ClickableLinePlot })
        self.chaco_plot.bgcolor = 'white'
        self.value_mapper = None
        self.index_mapper = None

        if len(self.data_x) == len(self.colors):
            colors = self.colors[:]
        else:
            colors = ['black'] * len(self.data_x)

        if self.flip_order:
            z = z[::-1]

        spacing = (z.max(axis=1) - z.min(axis=1)).min() * self.value_range
        offset = spacing * self.offset
        for i, (x_row, z_row) in enumerate(zip(x, z)):
            self.data.set_data('data_x_' + str(i), x_row)
            self.data.set_data('data_y_offset_' + str(i), z_row * self.value_range + offset * i)
            plots = self.chaco_plot.plot(('data_x_' + str(i), 'data_y_offset_' + str(i)), color=colors[i], type='line')
            plot = plots[0]
            self.container.add(plot)
            # Required for double-clicking plots
            plot.index.sort_order = 'ascending'
            plot.value.sort_order = 'ascending'

            if self.value_mapper is None:
                self.index_mapper = plot.index_mapper
                self.value_mapper = plot.value_mapper
            else:
                plot.value_mapper = self.value_mapper
                self.value_mapper.range.add(plot.value)
                plot.index_mapper = self.index_mapper
                self.index_mapper.range.add(plot.index)
        range = self.value_mapper.range
        range.high = (range.high - range.low) * self.value_range + range.low
        self.x_axis.mapper = self.index_mapper
        self.y_axis.mapper = self.value_mapper
        self.y_axis.title = 'Normalized intensity (%s)' % \
                get_value_scale_label(scale)
        self.zoom_tool = ClickUndoZoomTool(
            plot, tool_mode="box", always_on=True, pointer="cross",
            drag_button=settings.zoom_button,
            undo_button=settings.undo_button,
        )
        plot.overlays.append(self.zoom_tool)
        self.last_flip_order = self.flip_order
        return self.container

    def _reset_view(self):
        self.zoom_tool.revert_history_all()


class Surface2DPlot(ChacoPlot):
    def _prepare_data(self, datasets):
        stack = stack_datasets(datasets)
        x, y, z = bin_data(stack, 600)
        xi, yi, zi = cubic_interpolate(x, y, z, 600, 600)
        zi = np.clip(zi, 1, zi.max())
        return xi, yi, zi

    def _plot(self, x, y, z, scale):
        pd = ArrayPlotData()
        pd.set_data("imagedata", z)
        plot = Plot(pd, padding_left=60, fill_padding=True)
        plot.bgcolor = 'white'
        cmap = fix(jet, (0, z.max()))
        origin = 'bottom left' # origin = 'top left' # to flip y-axis
        plot.img_plot("imagedata", name="surface2d",
                      xbounds=(np.min(x), np.max(x)),
                      ybounds=(1.0, y[-1,-1]),
                      colormap=cmap, hide_grids=True, interpolation='nearest',
                      origin=origin,
                      )
        plot.default_origin = origin
        plot.x_axis.title = u'Angle (2\u0398)'

        tick_font = settings.tick_font
        plot.x_axis.title_font = settings.axis_title_font
        plot.y_axis.title_font = settings.axis_title_font
        plot.x_axis.tick_label_font = tick_font
        plot.y_axis.tick_label_font = tick_font
        plot.y_axis.title = "Dataset"
        plot.y_axis.tick_interval = 1.0
        actual_plot = plot.plots["surface2d"][0]

        self.plot_zoom_tool = ClickUndoZoomTool(
            plot, tool_mode="box", always_on=True, pointer="cross",
            drag_button=settings.zoom_button,
            undo_button=settings.undo_button,
            x_min_zoom_factor=-np.inf, y_min_zoom_factor=-np.inf,
        )
        plot.overlays.append(self.plot_zoom_tool)
        plot.tools.append(TraitsTool(plot))

        # Add a color bar
        colormap = actual_plot.color_mapper
        colorbar = ColorBar(index_mapper=LinearMapper(range=colormap.range),
                        color_mapper=colormap,
                        plot=actual_plot,
                        orientation='v',
                        resizable='v',
                        width=30,
                        padding=40,
                        padding_top=50,
                        fill_padding=True)

        colorbar._axis.title_font = settings.axis_title_font
        colorbar._axis.tick_label_font = settings.tick_font
        # Add pan and zoom tools to the colorbar
        self.colorbar_zoom_tool = ClickUndoZoomTool(colorbar,
                                                    axis="index",
                                                    tool_mode="range",
                                                    always_on=True,
                                                    drag_button=settings.zoom_button,
                                                    undo_button=settings.undo_button)
        pan_tool = PanToolWithHistory(colorbar,
                                      history_tool=self.colorbar_zoom_tool,
                                      constrain_direction="y", constrain=True,
                                      drag_button=settings.pan_button)
        colorbar.tools.append(pan_tool)
        colorbar.overlays.append(self.colorbar_zoom_tool)

        # Add a label to the top of the color bar
        colorbar_label = PlotLabel(
            u'Intensity\n{:^9}'.format('(' + get_value_scale_label(scale) + ')'),
            component=colorbar,
            font=settings.axis_title_font,
        )
        colorbar.overlays.append(colorbar_label)
        colorbar.tools.append(TraitsTool(colorbar))

        # Add the plot and colorbar side-by-side
        container = HPlotContainer(use_backbuffer=True)
        container.add(plot)
        container.add(colorbar)
        return container

    def _reset_view(self):
        self.plot_zoom_tool.revert_history_all()
        self.colorbar_zoom_tool.revert_history_all()

