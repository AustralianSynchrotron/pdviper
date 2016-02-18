"""
Writing a graphical application for scientific programming using TraitsUI
A step by step guide for a non-programmer

Author: Gael Varoquaux
Date: 2010-12-11
License: BSD

http://code.enthought.com/projects/traits/docs/html/tutorials/traits_ui_scientific_app.html#making-a-traits-editor-from-a-matplotlib-plot
"""
#import wx
from pyface.qt import QtGui, QtCore

#from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

try:
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar2QT
except ImportError:
    from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
#from traitsui.wx.editor import Editor
#from traitsui.wx.basic_editor_factory import BasicEditorFactory


from traitsui.qt4.editor import Editor
from traitsui.qt4.basic_editor_factory import BasicEditorFactory


class _MPLFigureEditor(Editor):
    scrollable  = True

    def init(self, parent):
        self.control = self._create_canvas(parent)
        self.set_tooltip()

    def update_editor(self):
        pass

    def _create_canvas(self,parent):
        """ Create the MPL canvas. """
        # The panel lets us add additional controls.
        frame = QtGui.QWidget()
        mpl_canvas = FigureCanvas(self.value)
        mpl_canvas.setParent(frame)
#        mpl_toolbar = NavigationToolbar2QT(mpl_canvas,frame)
        
        vbox=QtGui.QVBoxLayout()
        vbox.addWidget(mpl_canvas)
        #vbox.addWidget(mpl_toolbar)
        frame.setLayout(vbox)
        
        return frame
#        panel = wx.Panel(parent, -1, style=wx.CLIP_CHILDREN)
       # sizer = wx.BoxSizer(wx.VERTICAL)
        #panel.SetSizer(sizer)
        # matplotlib commands to create a canvas
        ##mpl_control = FigureCanvas(panel, -1, self.value)
        #sizer.Add(mpl_control, 1, wx.LEFT | wx.TOP | wx.GROW)
        #toolbar = NavigationToolbar2Wx(mpl_control)
        #sizer.Add(toolbar, 0, wx.EXPAND)
        #self.value.canvas.SetMinSize((10,10))
        #return panel


class MPLFigureEditor(BasicEditorFactory):
    klass = _MPLFigureEditor


if __name__ == "__main__":
    # Create a window to demo the editor
    from enthought.traits.api import HasTraits, Instance
    from enthought.traits.ui.api import View, Item
    from numpy import sin, cos, linspace, pi

    class Test(HasTraits):

        figure = Instance(Figure, ())

        view = View(Item('figure', editor=MPLFigureEditor(),
                                show_label=False),
                        width=400,
                        height=300,
                        resizable=True)

        def __init__(self):
            super(Test, self).__init__()
            axes = self.figure.add_subplot(111)
            t = linspace(0, 2*pi, 200)
            axes.plot(sin(t)*(1+0.5*cos(11*t)), cos(t)*(1+0.5*cos(11*t)))

    Test().configure_traits()

