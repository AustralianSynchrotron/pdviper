from numpy import array

from traits.api import Instance, Range, Bool
from traitsui.api import Item, UItem, VGroup, CustomEditor, DefaultOverride

from mpl_figure_editor import matplotlib_figure_editor
from matplotlib.figure import Figure
from traits_extensions import HasTraitsGroup

from processing import stack_datasets
from base_plot import BasePlot
from labels import get_value_scale_label


class MplPlot(BasePlot, HasTraitsGroup):
    figure = Instance(Figure, ())
    _draw_pending = Bool(False)

    azimuth = Range(-90, 90, -89)
    elevation = Range(0, 90, 14)
    quality = Range(0.0, 1.0, 0.1)
    group = VGroup(
        Item('azimuth',
             editor=DefaultOverride(mode='slider', auto_set=False, enter_set=True)),
        Item('elevation',
             editor=DefaultOverride(mode='slider', auto_set=False, enter_set=True)),
        Item('quality'),
        UItem('figure',
             editor=CustomEditor(matplotlib_figure_editor)),
    )

    def __init__(self, callback_obj=None, *args, **kws):
        super(MplPlot, self).__init__(*args, **kws)
        import matplotlib.pyplot as plt
        self.figure = plt.figure()
        self.figure.subplots_adjust(bottom=0, left=0, top=1, right=1)
        self.ax = None
        # This must be a weak reference, otherwise the entire app will
        # hang on exit.
        from weakref import proxy
        if callback_obj:
            self._callback_object = proxy(callback_obj)
        else:
            self._callback_object = lambda *args, **kw: None

    def close(self):
        del self._callback_object
        import matplotlib.pyplot as plt
        plt.close()

    def _azimuth_changed(self):
        self._perspective_changed()

    def _elevation_changed(self):
        self._perspective_changed()

    def _perspective_changed(self):
        if self.ax:
            self.ax.view_init(azim=self.azimuth, elev=self.elevation)
            self.redraw()

    def _quality_changed(self):
        self.redraw(replot=True)

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
        return x, y, z

    def _plot(self, x, y, z, scale='linear'):
        self.x, self.y, self.z = x, y, z
        self.scale = scale
        y_rows = z.shape[0]
        from mpl_toolkits.mplot3d import Axes3D
        from matplotlib.cm import jet
        self.figure.clear()
        ax = self.figure.add_subplot(111, projection='3d')
        ax.set_xlabel('Angle (2Theta)')
        ax.set_ylabel('Dataset')
        ax.set_zlabel('Intensity - %s' % get_value_scale_label(scale))
        ax.set_yticks(range(1, y_rows + 1), ((y_rows + 1) / 10) * 10)
        ax.view_init(azim=self.azimuth, elev=self.elevation)
        cstride = int((1.0 - self.quality) * y_rows + 1)
        ax.plot_surface(x, y, z,
                        rstride=200, cstride=cstride, linewidth=0,
                        cmap=jet, shade=False, antialiased=False)
        #self.figure.colorbar(surf, ax=ax, shrink=0.6, aspect=15)
        self.ax = ax
        self.figure.canvas.draw()
        return None

    def copy_to_clipboard(self):
        self.figure.canvas.Copy_to_Clipboard()

    def save_as(self, filename):
        self.figure.canvas.print_figure(filename)

    def __del__(self):
        import matplotlib.pyplot as plt
        plt.close()

