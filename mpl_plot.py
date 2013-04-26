import logger

import numpy as np
from numpy import array

from traits.api import Instance, Range, Bool, Float, Str, Enum, on_trait_change
from traitsui.api import Item, UItem, VGroup, HGroup, DefaultOverride
from traits_extensions import HasTraitsGroup

import matplotlib.pyplot as plt
from mpl_figure_editor import MPLFigureEditor
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d import Axes3D

from processing import stack_datasets, rebin_preserving_peaks
from base_plot import BasePlot
from labels import get_value_scale_label


MAX_QUALITY = 5

class MplPlot(BasePlot, HasTraitsGroup):
    figure = Instance(Figure, ())
    _draw_pending = Bool(False)

    scale = Enum('linear', 'log', 'sqrt')('linear')
    scale_values = ['linear', 'log', 'sqrt']    # There's probably a way to exract this from the Enum trait but I don't know how
    azimuth = Range(-90, 90, -70)
    elevation = Range(0, 90, 30)
    quality = Range(1, MAX_QUALITY, 1)
    flip_order = Bool(False)
    x_lower = Float(0.0)
    x_upper = Float
    x_label = Str('Angle (2$\Theta$)')
    y_label = Str('Dataset')
    z_lower = Float(0.0)
    z_upper = Float
    z_label = Str
    z_labels = {}   # A dictionary to hold edited labels for each scaling type

    group = VGroup(
        HGroup(
            VGroup(
                Item('azimuth',
                     editor=DefaultOverride(mode='slider', auto_set=False, enter_set=True)),
                Item('elevation',
                     editor=DefaultOverride(mode='slider', auto_set=False, enter_set=True)),
                Item('quality'),
                Item('flip_order'),
            ),
            VGroup(
                HGroup(
                    Item('x_label',
                         editor=DefaultOverride(auto_set=False, enter_set=True)),
                    Item('x_lower',
                         editor=DefaultOverride(auto_set=False, enter_set=True)),
                    Item('x_upper',
                         editor=DefaultOverride(auto_set=False, enter_set=True)),
                ),
                HGroup(
                    Item('y_label'),
                ),
                HGroup(
                    Item('z_label',
                         editor=DefaultOverride(auto_set=False, enter_set=True)),
                    Item('z_lower',
                         editor=DefaultOverride(auto_set=False, enter_set=True)),
                    Item('z_upper',
                         editor=DefaultOverride(auto_set=False, enter_set=True)),
                ),
            ),
        ),
        UItem('figure', editor=MPLFigureEditor()),
    )

    def __init__(self, callback_obj=None, *args, **kws):
        super(MplPlot, self).__init__(*args, **kws)
        self.figure = plt.figure()
        self.figure.subplots_adjust(bottom=0.05, left=0, top=1, right=0.95)
        self.ax = None
        for s in self.scale_values:
            self.z_labels[s] = 'Intensity - ' + get_value_scale_label(s, mpl=True)
        # This must be a weak reference, otherwise the entire app will
        # hang on exit.
        from weakref import proxy
        if callback_obj:
            self._callback_object = proxy(callback_obj)
        else:
            self._callback_object = lambda *args, **kw: None

    def close(self):
        del self._callback_object
        plt.close()

    def __del__(self):
        plt.close()

    @on_trait_change('azimuth, elevation')
    def _perspective_changed(self):
        if self.ax:
            self.ax.view_init(azim=self.azimuth, elev=self.elevation)
            self.redraw()

    def _quality_changed(self):
        self.redraw(replot=True)

    @on_trait_change('x_label, y_label, x_lower, x_upper, z_lower, z_upper, flip_order')
    def _trigger_redraw(self):
        self.quality = 1
        self.redraw(replot=True)

    def _z_label_changed(self):
        self.z_labels[self.scale] = self.z_label
        self._trigger_redraw()

    def redraw(self, replot=False, now=False):
        if not now and self._draw_pending:
            self._redraw_timer.Restart()
            return
        import wx
        canvas = self.figure.canvas
        if canvas is None:
            return
        def _draw():
            self._callback_object._on_redraw(drawing=True)
            if replot:
                self._plot(self.x, self.y, self.z, self.scale)
            else:
                canvas.draw()
            self._draw_pending = False
            self._callback_object._on_redraw(drawing=False)
        if now:
            _draw()
        else:
            self._redraw_timer = wx.CallLater(250, _draw)
            self._draw_pending = True
            self._redraw_timer.Start()

    def _prepare_data(self, datasets):
        stack = stack_datasets(datasets)
        x = stack[:,:,0]
        z = stack[:,:,1]
        y = array([ [i]*z.shape[1] for i in range(1, len(datasets) + 1) ])

        if x[0,0] < x[0,-1]:
            self.x_lower = x[0,0]
            self.x_upper = x[0,-1]
        else:
            self.x_lower = x[0,-1]
            self.x_upper = x[0,0]
        self.z_upper = z.max()
        return x, y, z


    def _plot(self, x, y, z, scale='linear'):
        self.x, self.y, self.z = x, y, z
        x, y, z = x.copy(), y.copy(), z.copy()

        if self.flip_order:
            z = z[::-1]
        self.scale = scale
        self.figure.clear()
        self.figure.set_facecolor('white')
        ax = self.ax = self.figure.add_subplot(111, projection='3d')
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        self.z_label = self.z_labels[self.scale]
        ax.set_zlabel(self.z_label)

        y_rows = z.shape[0]
        ax.locator_params(axis='y', nbins=10, integer=True)
        ax.view_init(azim=self.azimuth, elev=self.elevation)

        if self.quality != MAX_QUALITY:
            # map quality from 1->5 to 0.05->0.5 to approx. no. of samples
            samples = int(z.shape[1] * ((self.quality-1)*(0.5-0.05)/(5-1)+0.05))
            z, truncate_at, bins = rebin_preserving_peaks(z, samples/2)
            # Take the x's from the original x's to maintain visual x-spacing
            # We need to calculate the x's for the rebinned data
            x0_row = x[0,:truncate_at]
            old_xs = np.linspace(x0_row.min(), x0_row.max(), bins*2)
            new_xs = np.interp(old_xs, np.linspace(x0_row.min(), x0_row.max(), len(x0_row)), x0_row)
            x = np.tile(new_xs, (y.shape[0], 1))

        # Set values to inf to avoid rendering by matplotlib
        x[(x<self.x_lower) | (x>self.x_upper)] = np.inf
        z[(z<self.z_lower) | (z>self.z_upper)] = np.inf

        # separate series with open lines
        ys = y[:,0]
        points = []
        for x_row, z_row in zip(x, z):
            points.append(zip(x_row, z_row))
        lines = LineCollection(points)
        ax.add_collection3d(lines, zs=ys, zdir='y')
        ax.set_xlim3d(self.x_lower, self.x_upper)
        ax.set_ylim3d(1, y_rows)
        ax.set_zlim3d(self.z_lower, self.z_upper)
        self.figure.canvas.draw()
        return None

    def copy_to_clipboard(self):
        self.figure.canvas.Copy_to_Clipboard()

    def save_as(self, filename):
        self.figure.canvas.print_figure(filename)
        logger.logger.info('Saved plot {}'.format(filename))

    def _reset_view(self):
        self.azimuth = -70
        self.elevation = 30
