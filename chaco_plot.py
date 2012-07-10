import numpy as np
from numpy import array

from enable.api import Component
from traits.api import HasTraits, Instance

# Chaco imports
from chaco.api import Plot, ArrayPlotData, jet, ColorBar, LinearMapper, HPlotContainer
from chaco.tools.api import TraitsTool, PanTool
from chaco.default_colormaps import fix

from chaco_output import PlotOutput
from multi_line_plot import create_multi_line_plot
from tools import ClickUndoZoomTool

from processing import stack_datasets, interpolate_datasets, bin_data, cubic_interpolate

from base_plot import BasePlot



class ChacoPlot(BasePlot, HasTraits):
    component = Instance(Component)

    def redraw(self):
        self.component.request_redraw()

    def copy_to_clipboard(self):
        PlotOutput.copy_to_clipboard(self.component)

    def save_as(self, filename):
        PlotOutput.save_as_image(self.component, filename, change_bounds=False)


class StackedPlot(ChacoPlot):
    def _prepare_data(self, datasets):
        stack = stack_datasets(datasets)
        (x, z) = interpolate_datasets(stack, points=4800)
        x = array([x] * len(datasets))
        y = array([ [i] * z.shape[1] for i in range(1, len(datasets) + 1) ])
        return x, y, z

    def _plot(self, x, y, z, scale):
        num_plots = z.shape[0]
        # The multi-line plot code seems to omit 1 dataset from the y range,
        # so add a dummy dataset full of NaNs to make sure all datasets are
        # visible.
        y_limit = np.sum(np.nanmax(z, axis=1))
        y = np.linspace(0, y_limit, num_plots + 1)

        z = np.vstack([z, z.shape[1] * [np.nan]])
        plot = create_multi_line_plot(x[0], y, z, amplitude=2.0)
        return plot


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
        plot = Plot(pd)
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
        plot.x_axis.title = "Angle (2theta)"
        plot.y_axis.title = "Dataset"
        plot.y_axis.tick_interval = 1.0
        actual_plot = plot.plots["surface2d"][0]

        zoom = ClickUndoZoomTool(plot,
                        x_min_zoom_factor=-np.inf, y_min_zoom_factor=-np.inf,
                        tool_mode="box", always_on=True,
                        drag_button="right",
                        pointer="cross")
        plot.overlays.append(zoom)
        plot.tools.append(TraitsTool(plot))

        # Add a color bar
        colormap = actual_plot.color_mapper
        colorbar = ColorBar(index_mapper=LinearMapper(range=colormap.range),
                        color_mapper=colormap,
                        plot=actual_plot,
                        orientation='v',
                        resizable='v',
                        width=30,
                        padding=20)
        # Add pan and zoom tools to the colorbar
        pan_tool = PanTool(colorbar, constrain_direction="y", constrain=True)
        colorbar.tools.append(pan_tool)
        zoom_overlay = ClickUndoZoomTool(colorbar, axis="index", tool_mode="range",
                                always_on=True, drag_button="right")
        colorbar.overlays.append(zoom_overlay)

        # Add the plot and colorbar side-by-side
        container = HPlotContainer(use_backbuffer=True)
        container.add(plot)
        container.add(colorbar)
        return container

