from pyface.api import error
from chaco.api import PlotGraphicsContext, PlotGraphicsContextMixin

from output.svg import GraphicsContext as SVGGraphicsContext
from output.ps import PSGC

class SVGPlotGraphicsContext(PlotGraphicsContextMixin, SVGGraphicsContext):
    pass

class PSPlotGraphicsContext(PlotGraphicsContextMixin, PSGC):
    pass

class PlotOutput(object):
    @staticmethod
    def save_as_image(plot, filename, width=640, height=480, change_bounds=True):
        if change_bounds:
            old_bounds = plot.outer_bounds
            plot.outer_bounds = [width, height]
            plot.do_layout(force=True)
        else:
            width, height = plot.outer_bounds

        if filename.endswith('.svg'):
            gc = SVGPlotGraphicsContext((width, height), dpi=72)
        elif filename.endswith('.eps') or filename.endswith('.ps'):
            gc = PSPlotGraphicsContext((width, height), dpi=72)
        else:
            gc = PlotGraphicsContext((width, height), dpi=300)
        # Backbuffering apparently causes poor quality rendering of underlays
        backbuffer = plot.use_backbuffer
        plot.use_backbuffer = False
        gc.render_component(plot)
        plot.use_backbuffer = backbuffer

        try:
            gc.save(filename)
        except KeyError, e:
            errmsg = ("The filename must have an extension that matches "
                      "a graphics format, such as '.png' or '.tiff'.")
            if str(e.message) != '':
                errmsg = ("Unknown filename extension: '%s'\n" %
                          str(e.message)) + errmsg

            error(None, errmsg, title="Invalid Filename Extension")

        if change_bounds:
            plot.outer_bounds = old_bounds
            plot.do_layout(force=True)

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

