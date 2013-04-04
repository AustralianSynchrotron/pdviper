from traits.api import Str, List, Enum, Bool, Float, HasTraits, on_trait_change, Instance, \
                        Event, Button
from traitsui.api import View, Item, UItem, TableEditor, EnumEditor, Group, VGroup, HGroup, \
                        Label, Handler,Action
from traitsui.table_column import ObjectColumn
from fixes import fix_background_color
from processing_rescale import rescale_xye_datasets, write_xye_datasets
from traitsui.menu import OKButton, CancelButton

fix_background_color()


# Note - to get window to autoclose, apparently do this:
# https://mail.enthought.com/pipermail/enthought-dev/2011-February/028509.html
#class ClosingHandler(Handler):
#    def object_bt_rescale_changed(self, info):
#        new_wui = WavelengthEditor(datasets=info.object.datasets, filename_field=info.object.filename_field)
#        new_wui.edit_traits()
#        # rescale all x's between theta/d/Q
#        rescale_xye_datasets(self.datasets, self.target_value, self.convert_from, self.convert_to)
#        write_xye_datasets(self.datasets, self.filename_field)
#        # disable rescale button
#        info.ui.dispose()


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


class WavelengthEditorHandler(Handler):
    
    def do_rescale(self,info):
        rescale_xye_datasets(info.object.datasets, info.object.target_value, info.object.convert_from, info.object.convert_to)
        write_xye_datasets(info.object.datasets, info.object.filename_field)
        # disable rescale button
        #info.object.can_rescale = False 
        info.ui.dispose()
        return
        
        
        

class WavelengthEditor(HasTraits):
    datasets = List(WavelengthUI)
    filename_field = Str
    selected = List(WavelengthUI)
    can_rescale = Bool(True)

    x = Float(1.0)
    target_value = Float(1.0)
    #bt_rescale = Button("Rescale")

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

    rescale = Action(name = "Rescale",
                action = "do_rescale")


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
               # UItem('bt_rescale', enabled_when='can_rescale'),
               # enabled_when='can_rescale',
            ),
        ),
        resizable=True, width=0.5, height=0.5, kind='livemodal',
        title='Convert/scale abscissa',
        handler=WavelengthEditorHandler(),
        buttons=[rescale,CancelButton]
#        handler = ClosingHandler(),
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
        rescale_xye_datasets(self.datasets, self.target_value, self.convert_from, self.convert_to)
        write_xye_datasets(self.datasets, self.filename_field)
        # disable rescale button
        self.can_rescale = False

    @on_trait_change('x')
    def _trait_changed(self, trait, value):
        if not self.selecting:
            for obj in self.selected:
                setattr(obj, trait, value)
