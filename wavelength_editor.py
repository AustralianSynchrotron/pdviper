from traits.api import Str, List, Enum, Float, HasTraits, on_trait_change, Instance, \
                        Event, Button
from traitsui.api import View, Item, UItem, TableEditor, EnumEditor, Group, VGroup, HGroup, Label
from traitsui.table_column import ObjectColumn
from fixes import fix_background_color

fix_background_color()


class WavelengthUI(HasTraits):
    name = Str('')
    x = Float(1.0)
    dataset = Instance(object)
    traits_view = View(
        Item('name'),
        Item(ur'\u200Bx'),
    )


class WavelengthColumn(ObjectColumn):
    pass


class WavelengthEditor(HasTraits):
    datasets = List(WavelengthUI)
    selected = List(WavelengthUI)

    x = Float(1.0)
    target_value = Float(1.0)
    bt_rescale = Button("Rescale")

    convert_from = Enum('theta', 'd', 'Q')('theta')
    convert_to = Enum('theta', 'd', 'Q')('d')

    table_click = Event

    wavelength_editor = TableEditor(
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
            WavelengthColumn(name='name', cell_color='white', editable=False, width=0.9),
            WavelengthColumn(name='x'),
        ]
    )

    traits_view = View(
        VGroup(
            Item('datasets', editor=wavelength_editor, show_label=False),
            VGroup(
                Item('x', label='Modify selected X:'),
                HGroup(
                    Item('target_value'),
                    Group(
                        Item('convert_from',
                            style='custom',
                            editor=EnumEditor(values={
                                  'theta' : ur'1:\u0398',
                                  'd'     : ur'2:\u200Bd',
                                  'Q'     :   '3:Q',
                            }, cols=3),
                        label='From'),
                    ),
                    Group(
                        Item('convert_to',
                            style='custom',
                            editor=EnumEditor(values={
                                  'theta' : ur'1:\u0398',
                                  'd'     : ur'2:\u200Bd',
                                  'Q'     :   '3:Q',
                            }, cols=3),
                            label='To'),
                    ),
                ),
                UItem('bt_rescale'),
            ),
        ),
        resizable=True, width=0.5, height=0.5, kind='livemodal',
        title='Convert/scale abscissa'
    )

    def __init__(self, *args, **kwargs):
        self.datasets = map(lambda d: d.metadata['ui_w'], kwargs.pop('datasets'))
        super(WavelengthEditor, self).__init__(*args, **kwargs)
        self.wavelength_editor.on_select = self._selection_changed
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
        self.x = self.selected[0].x
        self.selecting = False

    def _bt_rescale_changed(self):
        # rescale all x's between theta/d/Q 
        self.peak_selecting = True

    @on_trait_change('x')
    def _trait_changed(self, trait, value):
        if not self.selecting:
            for obj in self.selected:
                setattr(obj, trait, value)
