from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit ='qt4'

from traits.api import Str, List, Bool, HasTraits, Color, on_trait_change, Instance, Event, Float

from traitsui.api import View, Item, TableEditor, VGroup, HGroup, Label
from traitsui.table_column import ObjectColumn
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.menu import OKButton, CancelButton

from fixes import fix_background_color, ColorEditor
fix_background_color()



class DatasetUI(HasTraits):
    name = Str('')
    color = Color(allow_none=True)
    active = Bool(True)
    markers = Bool(False)
    marker_size = Float(1.0)
    line_width = Float(1.0)
    dataset = Instance(object)

    traits_view = View(
        Item('name'),
        Item('color'),
        Item('active'),
        Item('markers'),
        Item('marker_size'),
        Item('line_width'),
    )


class DatasetColumn(ObjectColumn):
    pass

class ColorColumn(ObjectColumn):
    def get_cell_color(self, object):
        return getattr(object, self.name + '_')

    def get_value(self, object):
        return ''


class DatasetEditor(HasTraits):
    datasets = List(DatasetUI)
    selected = List(DatasetUI)

    color = Color
    active = Bool(True)
    markers = Bool(False)
    marker_size = Float(1.0)
    line_width = Float(1.0)

    table_click = Event

    dataset_editor = TableEditor(
        auto_size=True,
        selection_mode='rows',
        sortable=False,
        configurable=False,
        editable=True,
        edit_on_first_click=False,
        cell_bg_color='white',
        label_bg_color=(232,232,232),
        selection_bg_color=(232,232,232),
        columns=[
            DatasetColumn(name='name', cell_color='white', editable=False, width=0.9),
            ColorColumn(name='color'),
            CheckboxColumn(name='active'),
            CheckboxColumn(name='markers'),
            DatasetColumn(name='marker_size'),
            DatasetColumn(name='line_width'),
        ]
                                 
    )

    traits_view = View(
        VGroup(
            HGroup(Item('datasets', editor=dataset_editor, show_label=False)),
            VGroup(
                Label('Modify all selected items:'),
                VGroup(
                    Item('color', editor=ColorEditor()),
                    Item('active'),
                    Item('markers'),
                    Item('marker_size'),
                    Item('line_width'),
                    springy=True
                ),
            ),
            
        ),
        resizable=True, width=0.5, height=0.5, kind='livemodal',
        title='Edit datasets',
        buttons = [OKButton, CancelButton],
    )

    def __init__(self, *args, **kwargs):
        self.datasets = map(lambda d: d.metadata['ui'], kwargs.pop('datasets'))
        super(DatasetEditor, self).__init__(*args, **kwargs)
        self.dataset_editor.on_select = self._selection_changed
        self.selecting = False

    def _selection_changed(self, selected_objs):
        self.selected = selected_objs
        self._update_ui()

    def _table_click_changed(self, trait, value):
        self._update_ui()

    def _update_ui(self):
        if not self.selected:
            return
        self.selecting = True
        # If the colors are all the same
        if all(map(lambda o: o.color != None, self.selected)) and \
            len(set(map(lambda o: tuple(o.color), self.selected))) == 1:
            self.color = self.selected[0].color
        else:
            # This makes sure 'custom' is displayed
            self.color = (1,2,3,4)
        self.active = self.selected[0].active
        self.markers = self.selected[0].markers
        self.marker_size = self.selected[0].marker_size
        self.line_width = self.selected[0].line_width
        self.selecting = False

    @on_trait_change('active, color, markers, marker_size, line_width')
    def _trait_changed(self, trait, value):
        if not self.selecting:
            for obj in self.selected:
                setattr(obj, trait, value)


if __name__ == '__main__':
    d1 = DatasetUI(active=True, name='d1', color='red')
    d2 = DatasetUI(active=True, name='d2', color='green')
    d3 = DatasetUI(active=True, name='d3', color='blue')
    datasets = [ d1, d2, d3 ]
    dataset_editor = DatasetEditor(datasets=datasets)
    dataset_editor.configure_traits()

