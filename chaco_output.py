import logger
import os
from pyface.api import error

import numpy
from output.plot_graphics_context import PlotGraphicsContext, PlotGraphicsContextMixin
from output.mpl import GraphicsContext as MplGraphicsContext
from PySide.QtGui import QImage, QApplication, QClipboard, QColor
import PySide


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

    def get_dpi(self):
        return self.dpi

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
        if ext in ('svg', 'eps', 'pdf'):
            PlotOutput.save_with_matplotlib(plot, width, height, dpi, filename)
        else:
            PlotOutput.save_with_kiva(plot, width, height, dpi, filename, ext)

        if change_bounds:
            plot.outer_bounds = old_bounds

        plot.use_backbuffer = backbuffer
        plot.do_layout(force=True)
        plot.invalidate_draw()
        plot.request_redraw()

    @staticmethod
    def save_with_kiva(plot, width, height, dpi, filename, ext):
        gc = PlotGraphicsContext((width, height), dpi=dpi)
        gc.render_component(plot)
        gc.save(filename,file_format=ext)
        logger.logger.info('Saved plot {}'.format(filename))

    @staticmethod
    def save_with_matplotlib(plot, width, height, dpi, filename):
        from matplotlib.backend_bases import FigureCanvasBase
        figure = ChacoFigure(plot, width, height, dpi)
        canvas = FigureCanvasBase(figure)
        canvas.print_figure(filename)
        logger.logger.info('Saved plot {}'.format(filename))

    @staticmethod
    def copy_to_clipboard(plot):
        width, height = plot.outer_bounds

        gc = PlotGraphicsContext((width, height), dpi=72)
        backbuffer = plot.use_backbuffer
        plot.use_backbuffer = False
        gc.render_component(plot)
        plot.use_backbuffer = backbuffer

        # Create a bitmap the same size as the plot
        # and copy the plot data to it
        bmp = gc.bmp_array

        cache_bmp = bmp.tobytes()
        bitmap = QImage(cache_bmp, width+1, height+1, QImage.Format_RGB32)
        if QApplication.clipboard():
            QApplication.clipboard().setImage(bitmap.copy(), QClipboard.Clipboard)
        else:
            PySide.QtGui.QMessageBox("Unable to open the clipboard.", "Error")
