import numpy as np

from chaco.api import LinearMapper, Plot, PlotAxis, ArrayDataSource, DataRange1D
from chaco.multi_array_data_source import MultiArrayDataSource
from chaco.multi_line_plot import MultiLinePlot

def create_multi_line_plot_renderer(x_index, y_index, data, amplitude=0.5):
    # Create the data source for the MultiLinePlot.
    ds = MultiArrayDataSource(data=data)

    xs = ArrayDataSource(x_index, sort_order='ascending')
    xrange = DataRange1D()
    xrange.add(xs)

    ys = ArrayDataSource(y_index, sort_order='ascending')
    yrange = DataRange1D()
    yrange.add(ys)

    mlp = MultiLinePlot(
                    index=xs,
                    yindex=ys,
                    index_mapper=LinearMapper(range=xrange),
                    value_mapper=LinearMapper(range=yrange),
                    value=ds,
                    global_max=np.nanmax(data),
                    global_min=np.nanmin(data),
                    #use_global_bounds=True,
                    #default_origin='top left', origin='top left',
                    #**kw
    )
    mlp.normalized_amplitude = amplitude
    return mlp


def create_multi_line_plot(x_index, y_index, data, amplitude=0.5):
    mlp = create_multi_line_plot_renderer(x_index, y_index, data, amplitude)

    plot = Plot(title='Dataset')
    plot.add(mlp)

    x_axis = PlotAxis(component=plot,
                        mapper=mlp.index_mapper,
                        orientation='bottom',
                        title='2theta angle (degrees)')
    y_axis = PlotAxis(component=plot,
                        mapper=mlp.value_mapper,
                        orientation='left',
                        title='Normalized intensity (count)')
    plot.overlays.extend([x_axis, y_axis])
    return plot

