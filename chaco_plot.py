import logger
import numpy as np
from numpy import array

from enable.api import Component, ComponentEditor
from traits.api import Instance, Range, Bool, Int, on_trait_change
from traitsui.api import Group, UItem, VGroup, Item, HGroup
from chaco.api import Plot, ArrayPlotData, jet, ColorBar, LinearMapper, HPlotContainer, \
    PlotLabel, OverlayPlotContainer, LinePlot
from chaco.tools.api import TraitsTool
from chaco.default_colormaps import fix
from chaco.function_image_data import FunctionImageData

from chaco_output import PlotOutput
from tools import ClickUndoZoomTool, PanToolWithHistory
from processing import stack_datasets, interpolate_datasets, rebin_preserving_peaks, \
    bin_data, cubic_interpolate, regrid_data
from base_plot import BasePlot
from labels import get_value_scale_label
import settings
from traits_extensions import HasTraitsGroup
from raw_data_plot import MyPlotAxis
import scipy.interpolate
import scipy.ndimage



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
        self.x_axis = MyPlotAxis(component=self.container,
                          orientation='bottom',
                          title=u'Angle (2\u0398)',
                          title_font=settings.axis_title_font,
                          tick_label_font=settings.tick_font)
        y_axis_title = 'Normalized intensity (%s)' % get_value_scale_label('linear')
        self.y_axis = MyPlotAxis(component=self.container,
                          orientation='left',
                          title=y_axis_title,
                          title_font=settings.axis_title_font,
                          tick_label_font=settings.tick_font)
        self.container.overlays.extend([self.x_axis, self.y_axis])
        self.container.tools.append(
            TraitsTool(self.container, classes=[LinePlot,MyPlotAxis]))
        self.colors = []
        self.last_flip_order = self.flip_order

    @on_trait_change('offset, value_range, flip_order')
    def _replot_data(self):
        self._plot(self.data_x, None, self.data_z, self.scale)
        self.container.request_redraw()

    def _prepare_data(self, datasets):
        stack = stack_datasets(datasets)
        x = stack[:,:,0]
        z = stack[:,:,2]
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


def congrid(a, newdims, method='linear', centre=False, minusone=False):
    '''Arbitrary resampling of source array to new dimension sizes.
    Currently only supports maintaining the same number of dimensions.
    To use 1-D arrays, first promote them to shape (x,1).
    
    Uses the same parameters and creates the same co-ordinate lookup points
    as IDL''s congrid routine, which apparently originally came from a VAX/VMS
    routine of the same name.

    method:
    neighbour - closest value from original data
    nearest and linear - uses n x 1-D interpolations using
                         scipy.interpolate.interp1d
    (see Numerical Recipes for validity of use of n 1-D interpolations)
    spline - uses ndimage.map_coordinates

    centre:
    True - interpolation points are at the centres of the bins
    False - points are at the front edge of the bin

    minusone:
    For example- inarray.shape = (i,j) & new dimensions = (x,y)
    False - inarray is resampled by factors of (i/x) * (j/y)
    True - inarray is resampled by(i-1)/(x-1) * (j-1)/(y-1)
    This prevents extrapolation one element beyond bounds of input array.
    This routine from http://www.scipy.org/Cookbook/Rebinning
    '''
    if not a.dtype in [np.float64, np.float32]:
        a = np.cast[float](a)

    m1 = np.cast[int](minusone)
    ofs = np.cast[int](centre) * 0.5
    old = np.array( a.shape )
    ndims = len( a.shape )
    if len( newdims ) != ndims:
        print "[congrid] dimensions error. " \
              "This routine currently only support " \
              "rebinning to the same number of dimensions."
        return None
    newdims = np.asarray( newdims, dtype=float )
    dimlist = []

    if method == 'neighbour':
        for i in range( ndims ):
            base = np.indices(newdims)[i]
            dimlist.append( (old[i] - m1) / (newdims[i] - m1) \
                            * (base + ofs) - ofs )
        cd = np.array( dimlist ).round().astype(int)
        newa = a[list( cd )]
        return newa

    elif method in ['nearest','linear']:
        # calculate new dims
        for i in range( ndims ):
            base = np.arange( newdims[i] )
            dimlist.append( (old[i] - m1) / (newdims[i] - m1) \
                            * (base + ofs) - ofs )
        # specify old dims
        olddims = [np.arange(i, dtype = np.float) for i in list( a.shape )]

        # first interpolation - for ndims = any
        mint = scipy.interpolate.interp1d( olddims[-1], a, kind=method )
        newa = mint( dimlist[-1] )

        trorder = [ndims - 1] + range( ndims - 1 )
        for i in range( ndims - 2, -1, -1 ):
            newa = newa.transpose( trorder )

            mint = scipy.interpolate.interp1d( olddims[i], newa, kind=method )
            newa = mint( dimlist[i] )

        if ndims > 1:
            # need one more transpose to return to original dimensions
            newa = newa.transpose( trorder )

        return newa
    elif method in ['spline']:
        oslices = [ slice(0,j) for j in old ]
        oldcoords = np.ogrid[oslices]
        nslices = [ slice(0,j) for j in list(newdims) ]
        newcoords = np.mgrid[nslices]

        newcoords_dims = range(np.rank(newcoords))
        #make first index last
        newcoords_dims.append(newcoords_dims.pop(0))
        newcoords_tr = newcoords.transpose(newcoords_dims)
        # makes a view that affects newcoords

        newcoords_tr += ofs

        deltas = (np.asarray(old) - m1) / (newdims - m1)
        newcoords_tr *= deltas

        newcoords_tr -= ofs

        newa = scipy.ndimage.map_coordinates(a, newcoords)
        return newa
    else:
        print "Congrid error: Unrecognized interpolation type.\n", \
              "Currently only \'neighbour\', \'nearest\',\'linear\',", \
              "and \'spline\' are supported."
        return None


class Surface2DPlot(ChacoPlot):
    # The chaco window is updated based on the current zoom level as described here
    # http://www.digipedia.pl/usenet/thread/15882/127/
    # and here:
    # http://blog.powersoffour.org/2d-data-visualization-of-amr-with-matplotlib
    # and here:
    # http://svn.enzotools.org/yt/trunk/yt/extensions/image_panner/pan_and_scan_widget.py

    twod_plot = Instance(Component)
    img_plot = Instance(Component)
    sidelength = Int(1000)


    def _prepare_data(self, datasets):
        '''
        This is called as the 2d chaco plot window is being set up. The return values
        are not used for plotting but are used for getting the tick marker scales and
        colorbar scale.
        I bin it down to a small arbitrary number of bins to keep things fast.
        '''
        self.update_content = True
        stack = stack_datasets(datasets)
        self.dataset_stack = stack
        BINS = 4
        xi, yi, zi = bin_data(stack, BINS)
        return xi, yi, zi


    def _prepare_data_for_window(self, xlow, xhigh, ylow, yhigh):
        '''
        This is called every time the chaco window is rendered and it dynamically
        computes and returns the data corresponding to the window limits. This allows
        rendering to stay relatively fast since data is binned down to a resolution
        roughly matching what the window can usefully display. 
        '''
        if not self.update_content:
            return self.zi
        stack = self.dataset_stack.copy()

        # deal with restricted y-range
        if ylow < 1 or ylow >= yhigh:
            ylow = 1
        if yhigh > stack.shape[0] or yhigh <= ylow:
            yhigh = stack.shape[0]
        stack = stack[int(np.round(ylow-1)):int(np.round(yhigh))]

        if stack[0,0,0] > stack[0,-1,0]:
            stack = stack[:,::-1,:]

        # get a typical interval
        interval = np.median(np.diff(stack[0,:10,0]))

        # get a region a couple of samples bigger on each side of the window to allow for
        # misalignment
        xs = stack[:,:,0]
        xlow_expanded = xs[0,0] - interval*2
        xhigh_expanded = xs[0,-1] + interval*2
        column_mask = (xs[0]>=xlow_expanded) & (xs[0]<=xhigh_expanded)
        stack = stack[:,column_mask][np.newaxis].reshape(xs.shape[0],-1,3)

        # regrid all rows - use an interval half that of the original interval to minimise interpolation errors
        first_row = regrid_data(stack[0], start=xlow_expanded, end=xhigh_expanded, interval=interval/2)
        new_stack = np.empty((xs.shape[0], first_row.shape[0], 3))
        new_stack[0] = first_row
        for i, stack_row in enumerate(stack[1:]):
            new_stack[i+1] = regrid_data(stack_row, start=xlow_expanded, end=xhigh_expanded, interval=interval/2)

        # new_stack is the regridded version so window it properly
        xs = new_stack[:,:,0]
        zs = new_stack[:,:,1]
        mask = (xs[0]>=xlow) & (xs[0]<=xhigh)
        zs = zs[:,mask].reshape(zs.shape[0],-1)

        YBINS = zs.shape[0]*10
        BINS = min(1000, zs.shape[1])
        zi = congrid(zs, (YBINS, BINS), method='neighbour', minusone=True)

        zi = np.clip(zi, 1, zi.max())

        self.zi = zi
        return zi


    @on_trait_change('twod_plot.range2d.updated')
    def _update_ranges(self):
        self.update_content = not self.update_content
        if self.img_plot is not None:
            low_xy = self.twod_plot.range2d.low
            high_xy = self.twod_plot.range2d.high
            self.img_plot.index.set_data(
                np.linspace(low_xy[0], high_xy[0], self.sidelength),
                np.linspace(low_xy[1], high_xy[1], self.sidelength),
                ('ascending', 'ascending'),
            )

    def _plot(self, x, y, z, scale):
        pd = ArrayPlotData()
        pd.set_data("imagedata", z)
        plot = Plot(pd, padding_left=60, fill_padding=True)
        plot.bgcolor = 'white'
        cmap = fix(jet, (0, z.max()))
        origin = 'bottom left' # origin = 'top left' # to flip y-axis

        fid = FunctionImageData(func=self._prepare_data_for_window, data_range=plot.range2d)
        pd.set_data("imagedata", fid)

        self.img_plot = plot.img_plot("imagedata", name="surface2d",
                      xbounds=(np.min(x), np.max(x)),
                      ybounds=(1.0, y[-1,-1]),
                      colormap=cmap, hide_grids=True, interpolation='nearest',
                      origin=origin,
                      )[0]
        plot.default_origin = origin
        plot.x_axis = MyPlotAxis(component=plot, orientation='bottom')
        plot.y_axis = MyPlotAxis(component=plot, orientation='left')
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
            plot, always_on=True, pointer="cross",
            tool_mode="range",
            axis="index",
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
        self.twod_plot = plot
        return container

    def _reset_view(self):
        self.plot_zoom_tool.revert_history_all()
        self.colorbar_zoom_tool.revert_history_all()
        self.update_content = True
