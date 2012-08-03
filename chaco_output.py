import os
from pyface.api import error

from output.plot_graphics_context import PlotGraphicsContext, PlotGraphicsContextMixin
from output.mpl import GraphicsContext as MplGraphicsContext


class MplPlotGraphicsContext(PlotGraphicsContextMixin, MplGraphicsContext):
    def __init__(self, size, dpi, format='svg', renderer=None):
        PlotGraphicsContextMixin.__init__(self, size, dpi=dpi)
        MplGraphicsContext.__init__(self, size, dpi=dpi, format=format, renderer=renderer)


class ChacoFigure(object):
    def __init__(self, plot, width, height, dpi=72):
        self.plot = plot
        self.width = width
        self.height = height
        class BBox(object):
            pass
        self.bbox = BBox()
        self.bbox.width = width
        self.bbox.height = height
        self.bbox.bounds = 0, 0, width, height
        self.dpi = dpi
        self.facecolor = (255, 255, 255)
        self.edgecolor = (255, 255, 255)

    def set_canvas(self, canvas):
        self.canvas = canvas

    def set_dpi(self, dpi):
        self.dpi = dpi

    def get_size_inches(self):
        return self.width / float(self.dpi), self.height / float(self.dpi)

    def get_facecolor(self):
        return self.facecolor

    def get_edgecolor(self):
        return self.edgecolor

    def set_facecolor(self, facecolor):
        self.facecolor = facecolor

    def set_edgecolor(self, edgecolor):
        self.edgecolor = edgecolor

    def draw(self, renderer):
        gc = MplPlotGraphicsContext((self.width, self.height), self.dpi, renderer=renderer)
        gc.render_component(self.plot)


class PlotOutput(object):
    @staticmethod
    def save_as_image(plot, filename, width=960, height=720, dpi=300, change_bounds=True):
        # Backbuffering apparently causes poor quality rendering of underlays
        backbuffer = plot.use_backbuffer
        plot.use_backbuffer = False

        if change_bounds:
            old_bounds = plot.outer_bounds
            plot.outer_bounds = [width, height]
            plot.do_layout(force=True)
        else:
            width, height = plot.outer_bounds

        plot.invalidate_draw()
        plot.request_redraw()

        ext = os.path.splitext(filename)[1][1:]
        if ext in ( 'svg', 'eps', 'pdf' ):
            PlotOutput.save_with_matplotlib(plot, width, height, dpi, filename)
        else:
            PlotOutput.save_with_kiva(plot, width, height, dpi, filename)

        if change_bounds:
            plot.outer_bounds = old_bounds

        plot.use_backbuffer = backbuffer
        plot.do_layout(force=True)
        plot.invalidate_draw()
        plot.request_redraw()

    @staticmethod
    def save_with_kiva(plot, width, height, dpi, filename):
        gc = PlotGraphicsContext((width, height), dpi=dpi)
        gc.render_component(plot)
        gc.save(filename)

    @staticmethod
    def save_with_matplotlib(plot, width, height, dpi, filename):
        from matplotlib.backend_bases import FigureCanvasBase
        figure = ChacoFigure(plot, width, height, dpi)
        canvas = FigureCanvasBase(figure)
        ext = os.path.splitext(filename)[1][1:]

        try:
            # Call the relevant print_ method on the canvas.
            # This invokes the correct backend and prints the "figure".
            func = getattr(canvas, 'print_' + ext)
        except AttributeError, e:
            errmsg = ("The filename must have an extension that matches "
                      "a graphics format, such as '.png' or '.tiff'.")
            if str(e.message) != '':
                errmsg = ("Unknown filename extension: '%s'\n" %
                          str(e.message)) + errmsg
            error(None, errmsg, title="Invalid Filename Extension")
        else:
            # Call the function
            func(filename)

    @staticmethod
    def copy_to_clipboard(plot):
        # WX specific, though QT implementation is similar using
        # QImage and QClipboard
        import wx

        width, height = plot.outer_bounds

        gc = PlotGraphicsContext((width, height), dpi=72)
        backbuffer = plot.use_backbuffer
        plot.use_backbuffer = False
        gc.render_component(plot)
        plot.use_backbuffer = backbuffer

        # Create a bitmap the same size as the plot
        # and copy the plot data to it
        bmp = gc.bmp_array
        if gc.format().startswith('bgra'):
            bmp_rgba = bmp[:,:,[2,1,0,3]]
        else:
            bmp_rgba = bmp
        bitmap = wx.BitmapFromBufferRGBA(width+1, height+1,
                                     bmp_rgba.flatten())
        data = wx.BitmapDataObject()
        data.SetBitmap(bitmap)

        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(data)
            wx.TheClipboard.Close()
        else:
            wx.MessageBox("Unable to open the clipboard.", "Error")

