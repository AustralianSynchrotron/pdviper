from traits.api import Str, List, Bool, HasTraits, Color, on_trait_change, Instance, Event, Float

from traitsui.api import View, Item, UItem, TableEditor, VGroup, HGroup, Label,ListEditor, Group,Action, Handler
from traitsui.table_column import ObjectColumn,NumericColumn
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.menu import OKButton, CancelButton
from traits.api import List, Str, Float, HasTraits, Instance, Button, Enum, Bool, \
                        DelegatesTo, Range, HTML, Int
from traitsui.tabular_adapter import TabularAdapter       
from fixes import fix_background_color, ColorEditor
fix_background_color()
from xye import XYEDataset
from peak_fitting import fit_peaks_background, createPeakRows, PeakRowUI
import re



def createDatasetPeaks(datasets):
    datasetPeakList=[]
    for d in datasets:
        peaklist=createPeakRows(d.fit_params)
        dspeaks=DatasetPeaks(peaks=peaklist,name=d.name,dataset=d)
        datasetPeakList.append(dspeaks)
    return datasetPeakList


class PeakColumn(ObjectColumn):
    pass

class DatasetPeaks(HasTraits):
    peaks = List(PeakRowUI)
    name=Str
    dataset=Instance(XYEDataset)
    #background={}
    peak_editor=TableEditor(
        auto_size=True,
        selection_mode='cells',
        sortable=False,
        editable=True,
        deletable=True,
        edit_on_first_click=False,
        cell_bg_color='white',
        label_bg_color=(232,232,232),
        selection_bg_color=(232,232,232),
        columns=[
            PeakColumn(name='peak_number', cell_color='white', editable=False, width=0.9),
            CheckboxColumn(name='fit', label="Refine?"),
            NumericColumn(name='position', label="Position", cell_color='white', editable=True),
            NumericColumn(name='intensity',label='Intensity',cell_color='white', editable=True),
            NumericColumn(name='sigma',label='Sigma',cell_color='white', editable=True),
            NumericColumn(name='gamma',label='Gamma',cell_color='white', editable=True),
        ],
        show_toolbar=True,
        row_factory=PeakRowUI                     
    )

    traits_view=View(
        UItem('name'),
        UItem('peaks', editor=peak_editor),
    )

    def to_dict(self):
        newdict={}
        for pr in self.peaks:
            newdict.update(pr.row_to_dict())
        return newdict



class PeakFitEditorHandler(Handler):
    
    varyList=[r'Back:',r'int',r'sig',r'gam']
    
    def object__close_changed(self, info):
        print info
    
    def update_peak_list(self,dspeaks,params):
        thisdict= dspeaks.to_dict()
        removeregexList=[r'int',r'pos',r'sig',r'gam']
        removeList=[key for regex in removeregexList for key in params.keys() if re.search(regex,key)]
        for r in removeList:
            params.pop(r)
        params.update(thisdict)    
       
            
    def do_refine(self,info):
        self.update_peak_list(info.object.selected,info.object.selected.dataset.fit_params)
        print 'refining...'
        dataset=info.object.selected.dataset
        for pr in info.object.selected.peaks:
            if pr.fit is False:
                info.object.selected.peaks.remove(pr)     
        background,new_params=fit_peaks_background(info.object.selected.peaks,self.varyList,dataset,None,dataset.fit_params)
        dataset.background=background
        dataset.fit_params=new_params
        print new_params
        # update the peaks list
        newPeaks=createPeakRows(new_params)
        info.object.update_editor()
        
            
        
class PeakFittingEditor(HasTraits):
    
    datasets=List(XYEDataset)
    dataset_peaks=List(DatasetPeaks)
    selected=Instance(DatasetPeaks)
    index = None

    refine = Action(name = "Refine",
                action = "do_refine")
    

    
    traits_view = View(
        
        Item('dataset_peaks@', editor=ListEditor(use_notebook=True, deletable=False, page_name='.name',selected='selected'), show_label=False),
            #VGroup(
                #Label('Modify all selected items:'),
            #    VGroup(
            #        Item('name'),
             #       Item('peaks', editor=peak_editor),
            #        springy=True
             #   ),
     #       ),
            
        
        resizable=True, width=0.5, height=0.5, kind='livemodal',
        title='Edit peaks to fit',
        handler=PeakFitEditorHandler(),
        buttons=[refine, OKButton,CancelButton]
               
    )
    
    def __init__(self, *args, **kwargs):        
        super(PeakFittingEditor, self).__init__(*args, **kwargs)
        self.dataset_peaks=createDatasetPeaks(self.datasets)
        self.index=Range(0,len(self.dataset_peaks)-1,mode='spinner')
        self.selected=self.dataset_peaks[0]
    
    def _selected_changed(self, selected):
        self.index = self.dataset_peaks.index(selected)
        

    def _index_changed(self, index):
        self.selected = self.dataset_peaks[ index ]
        
        
        # For now we will do only the selected dataset, the one that is the top tab that is visible see how long it takes, then loop around the other 
        # datasets if need be
        # remove peaks from fit_params if they are not ticked to refine
        # do the least squares refinement on the data with those params
        # update the display of the table. Clicking ok, "saves" the params for that dataset
        #
       
    def _bt_myclosed_changed(self):
        pass
    