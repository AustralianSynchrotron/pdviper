from traits.api import Str, List, HasTraits, Instance, Float

from traitsui.api import View, Item, TableEditor, VGroup, HGroup, Label, UItem
from enable.api import ComponentEditor
from traitsui.table_column import ObjectColumn
from chaco.api import Plot, ArrayPlotData

from fixes import fix_background_color
fix_background_color()

from xye import XYEDataset
from tools import ClickUndoZoomTool
import settings
import numpy as np

class DatasetPair(HasTraits):
    first_name = Str
    second_name = Str
    first = XYEDataset
    second = XYEDataset
    peak_diff = Float

    def __init__(self, *args, **kwargs):
        super(DatasetPair, self).__init__(*args, **kwargs)
        self.first_name = self.first.name
        self.second_name = self.second.name
        self.peak_diff = self.first.metadata['peak_fit'] - self.second.metadata['peak_fit']

class PeakFitWindow(HasTraits):
    pairs = List(DatasetPair)
    selected = Instance(DatasetPair)

    plot = Plot

    table_editor = TableEditor(
        auto_size=True,
        selection_mode='row',
        sortable=False,
        configurable=False,
        editable=False,
        cell_bg_color='white',
        label_bg_color=(232,232,232),
        selection_bg_color=(232,232,232),
        columns=[
            ObjectColumn(label='First position', name='first_name', cell_color='white', width=0.33),
            ObjectColumn(label='Second position', name='second_name', cell_color='white', width=0.33),
            ObjectColumn(label='Peak difference', name='peak_diff', cell_color='white', width=0.33),
        ]
    )

    traits_view = View(
        HGroup(
            Item('pairs', editor=table_editor, show_label=False),
            UItem('plot', editor=ComponentEditor(bgcolor='white')),
        ),
        resizable=True, width=0.75, height=0.5, kind='livemodal',
        title='View peak fits'
    )

    def __init__(self, *args, **kwargs):
        self.pairs = [ DatasetPair(first=d1, second=d2) for d1, d2 in kwargs['dataset_pairs'] ]
        self.pairs.sort(key=lambda pair: pair.first.name)
        self.range = kwargs.pop('range')
        super(PeakFitWindow, self).__init__(*args, **kwargs)
        self.table_editor.on_select = self._selection_changed
        self.selected = self.pairs[0] if self.pairs else None
        self.data = ArrayPlotData()
        self.plot = Plot(self.data)
        self.zoom_tool = ClickUndoZoomTool(self.plot,
                        tool_mode="box", always_on=True,
                        drag_button=settings.zoom_button,
                        undo_button=settings.undo_button,
                        zoom_to_mouse=True)
        self.plot.overlays.append(self.zoom_tool)
        self.plot_ymin = np.inf
        self.plot_ymax = -np.inf
        for pair in self.pairs:
            self._plot_dataset(pair.first)
            self._plot_dataset(pair.second, offset=pair.peak_diff)
#        self.plot.request_redraw()

    def _selection_changed(self, selected_objs):
        if self.selected:
            self.plot.plots[self.selected.first.name][0].visible = False
            self.plot.plots[self.selected.second.name][0].visible = False
        self.selected = selected_objs
        if self.selected is None:
            return
        self.plot.plots[self.selected.first.name][0].visible = True
        self.plot.plots[self.selected.second.name][0].visible = True
        self.plot.request_redraw()

    def _plot_dataset(self, dataset, offset=0.0):
        x, y = dataset.data[:,[0,1]].T
        self.data.set_data(dataset.name + '_x', x + offset)
        self.data.set_data(dataset.name + '_y', y)
        plot = self.plot.plot((dataset.name + '_x', dataset.name + '_y'),
                              type='line',
                              color=dataset.metadata['ui'].color,
                              name=dataset.name,
                              visible=False)
        range = plot[0].index_mapper.range
        range.low, range.high = self.range
        pvr = plot[0].value_range
        y_in_range = y[(x>range.low) & (x<range.high)]
        self.plot_ymin = min(self.plot_ymin, y_in_range.min())
        self.plot_ymax = max(self.plot_ymax, y_in_range.max())
        pvr.low_setting, pvr.high_setting = self.plot_ymin, self.plot_ymax
        pvr.refresh()
