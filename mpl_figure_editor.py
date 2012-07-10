"""
http://www.scipy.org/Cookbook/EmbeddingInTraitsGUI

A simple demonstration of embedding a matplotlib plot window in 
a traits-application. The CustomEditor allow any wxPython window
to be used as an editor. The demo also illustrates Property traits,
which provide nice dependency-handling and dynamic initialisation, using
the _xxx_default(...) method.
"""

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
#from matplotlib.backends.backend_wx import NavigationToolbar2Wx

import wx

def matplotlib_figure_editor(parent, editor):
    """
    Builds the Canvas window for displaying the mpl-figure
    """
    fig = editor.object.figure
    panel = wx.Panel(parent, -1)
    canvas = FigureCanvasWxAgg(panel, -1, fig)
    #toolbar = NavigationToolbar2Wx(canvas)
    #toolbar.Realize()

    sizer = wx.BoxSizer(wx.VERTICAL)
    sizer.Add(canvas,1,wx.EXPAND|wx.ALL,1)
    #sizer.Add(toolbar,0,wx.EXPAND|wx.ALL,1)
    panel.SetSizer(sizer)
    return panel

