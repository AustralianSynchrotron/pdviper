from numpy import inf
import numpy as np

from enable.api import Component
from traits.api import HasTraits, Instance

from chaco.api import Plot, ArrayPlotData, Legend
from chaco.tools.api import TraitsTool, SimpleInspectorTool, RangeSelection, RangeSelectionOverlay
from chaco.overlays.api import SimpleInspectorOverlay

from tools import ClickUndoZoomTool, KeyboardPanTool, PointerControlTool, LineInspectorTool
from processing import rescale
from labels import get_value_scale_label
import settings


class RawDataPlot(HasTraits):
    plot = Instance(Component)

    def __init__(self, datasets):
        self.plots = {}
        self._setup_plot()

    def plot_datasets(self, datasets, scale='linear'):
        if self.plots:
            self.plot.delplot(*self.plots.keys())
            self.plots = {}
        for name, dataset in datasets.iteritems():
            data = dataset.data
            x, y = np.transpose(data[:, [0,1]])
            self.plot_data.set_data(name + '_x', x)
            self.plot_data.set_data(name + '_y', rescale(y, method=scale))
            plot = self.plot.plot((name + '_x', name + '_y'),
                                  name=name, type='line', color='auto')
            self.plots[name] = plot

        if len(datasets) > 0:
            self.plot0renderer = plot[0]
            self.range_selection_tool = RangeSelection(self.plot0renderer, left_button_selects=True)
            self.range_selection_overlay = RangeSelectionOverlay(component=self.plot0renderer)

        self.reset_view()
        self.show_legend(True)
        self._set_scale(scale)

    def reset_view(self):
        self.plot.index_range.reset()
        self.plot.value_range.reset()
        self.zoom_tool.clear_undo_history()

    def _set_scale(self, scale):
        self.plot.y_axis.title = 'Intensity (%s)' % get_value_scale_label(scale)

    def show_legend(self, visible=True):
        self.plot.legend.visible = visible

    def show_grids(self, visible=True):
        self.plot.x_grid.visible = visible
        self.plot.y_grid.visible = visible

    def show_crosslines(self, visible=True):
        for crossline in self.crosslines:
            crossline.visible = visible
        if visible:
            self.pointer_tool.inner_pointer = 'blank'
        else:
            self.pointer_tool.inner_pointer = 'cross'

    def get_plot(self):
        return self.plot

    def add_range_selection_tool(self):
        self.plot0renderer.tools.append(self.range_selection_tool)
        self.plot0renderer.overlays.append(self.range_selection_overlay)

    def remove_range_selection_tool(self):
        self.plot0renderer.tools.remove(self.range_selection_tool)
        self.plot0renderer.overlays.remove(self.range_selection_overlay)

    def get_range_selection_tool_limits(self):
        return self.range_selection_tool._get_selection()

    def _setup_plot(self):
        self.plot_data = ArrayPlotData()
        self.plot = Plot(self.plot_data,
            padding_left=120, fill_padding=True,
            bgcolor="white", use_backbuffer=True)

        self._setup_plot_tools(self.plot)

        # Recreate the legend so it sits on top of the other tools.
        self.plot.legend = Legend(component=self.plot,
                                  padding=10,
                                  error_icon='blank',
                                  visible=False,
                                  plots=self.plots)

        self.plot.x_axis.title = ur'Angle (2\u0398)'
        tick_font = settings.tick_font
        self.plot.x_axis.title_font = settings.axis_title_font
        self.plot.y_axis.title_font = settings.axis_title_font
        self.plot.x_axis.tick_label_font = tick_font
        self.plot.y_axis.tick_label_font = tick_font
        #self.plot.x_axis.tick_out = 0
        #self.plot.y_axis.tick_out = 0
        self._set_scale('linear')

        # Add the traits inspector tool to the container
        self.plot.tools.append(TraitsTool(self.plot))

    def _setup_plot_tools(self, plot):
        """Sets up the background, and several tools on a plot"""
        plot.bgcolor = "white"

        # The ZoomTool tool is stateful and allows drawing a zoom
        # box to select a zoom region.
        self.zoom_tool = ClickUndoZoomTool(plot,
                        x_min_zoom_factor=-inf, y_min_zoom_factor=-inf,
                        tool_mode="box", always_on=True,
                        drag_button=settings.zoom_button,
                        undo_button=settings.undo_button,
                        zoom_to_mouse=True)

        # The PanTool allows panning around the plot
        self.pan_tool = KeyboardPanTool(plot, drag_button=settings.pan_button,
                                        history_tool=self.zoom_tool)

        plot.tools.append(self.pan_tool)
        plot.overlays.append(self.zoom_tool)

        x_crossline = LineInspectorTool(component=plot,
                                    axis='index_x',
                                    inspect_mode="indexed",
                                    is_listener=False,
                                    color="grey")
        y_crossline = LineInspectorTool(component=plot,
                                    axis='index_y',
                                    inspect_mode="indexed",
                                    color="grey",
                                    is_listener=False)
        plot.overlays.append(x_crossline)
        plot.overlays.append(y_crossline)
        self.crosslines = (x_crossline, y_crossline)

        # The RangeSelectionTool tool is stateful and allows selection of a candidate
        # range for dataseries alignment.
#        plot.overlays.append(RangeSelectionOverlay(component=plot))

        tool = SimpleInspectorTool(plot)
        plot.tools.append(tool)
        overlay = SimpleInspectorOverlay(component=plot, inspector=tool, align="lr")
        def formatter(**kw):
            return '(%.2f, %.2f)' % (kw['x'], kw['y'])
        overlay.field_formatters = [[formatter]]
        overlay.alternate_position = (-25, -25)
        plot.overlays.append(overlay)

        self.pointer_tool = PointerControlTool(component=plot, pointer='arrow')
        plot.tools.append(self.pointer_tool)


