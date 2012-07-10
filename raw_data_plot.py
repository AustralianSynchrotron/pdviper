from numpy import inf
import numpy as np

from enable.api import Component
from traits.api import HasTraits, Instance

from chaco.api import Plot, ArrayPlotData, add_default_axes, add_default_grids, PlotLabel
from chaco.tools.api import TraitsTool, SimpleInspectorTool
from chaco.overlays.api import SimpleInspectorOverlay

from tools import ClickUndoZoomTool, KeyboardPanTool
from processing import rescale


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
        self.plot.index_range.reset()
        self.plot.value_range.reset()
        self.zoom_tool.clear_undo_history()
        #self.pan_tool.restrict_to_data = True
        self._tools_visible(True)
        #self.plot.value_scale = scale

    def _tools_visible(self, visible=True):
        self.plot.legend.visible = visible

    def get_plot(self):
        return self.plot

    def _setup_plot(self):
        self.plot_data = ArrayPlotData()
        self.plot = Plot(self.plot_data,
            padding_left=50, fill_padding=True,
            bgcolor="white", use_backbuffer=True)

        self._setup_plot_tools(self.plot)

        self.plot.legend.plots = self.plots
        self.plot.legend.visible = False

        self.plot.x_axis.title = "Angle (2theta)"
        self.plot.y_axis.title = "Intensity (count)"

        # Add the title at the top
        self.plot.overlays.append(PlotLabel("XYE data",
                                       component=self.plot,
                                       font="swiss 16",
                                       overlay_position="top"))

        # Add the traits inspector tool to the container
        self.plot.tools.append(TraitsTool(self.plot))

    def _setup_plot_tools(self, plot):
        """Sets up the background, and several tools on a plot"""
        # Make a white background with grids and axes
        plot.bgcolor = "white"
        plot.pointer = "cross"

        add_default_grids(plot)
        add_default_axes(plot)

        # The PanTool allows panning around the plot
        self.pan_tool = KeyboardPanTool(plot, drag_button="left")
        plot.tools.append(self.pan_tool)

        # The ZoomTool tool is stateful and allows drawing a zoom
        # box to select a zoom region.
        self.zoom_tool = ClickUndoZoomTool(plot,
                        x_min_zoom_factor=-inf, y_min_zoom_factor=-inf,
                        tool_mode="box", always_on=True,
                        drag_button="right", #axis="index",
                        pointer="cross")
        plot.overlays.append(self.zoom_tool)

        tool = SimpleInspectorTool(plot)
        plot.tools.append(tool)
        overlay = SimpleInspectorOverlay(component=plot, inspector=tool, align="lr")
        def formatter(**kw):
            return '(%.2f, %.2f)' % (kw['x'], kw['y'])
        overlay.field_formatters = [[formatter]]
        overlay.alternate_position = (-25, -25)
        plot.overlays.append(overlay)

