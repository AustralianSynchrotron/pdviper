import numpy as np

from chaco.api import LinearMapper, ArrayDataSource, DataRange1D
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

