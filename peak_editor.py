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
from peak_fitting import fit_peaks_background, createPeakRows, PeakRowUI,autosearch_peaks,updatePeakRows
import re
from chaco.tools.api import LineSegmentTool
from copy import deepcopy
from ui_helpers import get_txt_filename
import numpy as np


def createDatasetPeaks(dataset):
    peaklist=createPeakRows(dataset.select_peaks_params)
    dspeaks=DatasetPeaks(peaks=peaklist,name=dataset.name,dataset=dataset)
    
    return dspeaks


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
            NumericColumn(name='fwhm',label='FWHM',cell_color='white', editable=False)
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

def update_peak_list(dspeaks,params):
        thisdict= dspeaks.to_dict()
        removeregexList=[r'int',r'pos',r'sig',r'gam']
        removeList=[key for regex in removeregexList for key in params.keys() if re.search(regex,key)]
        for r in removeList:
            params.pop(r)
        params.update(thisdict)    

def update_peak_list_by_list(peaklist,params):        
        removeregexList=[r'int',r'pos',r'sig',r'gam']
        removeList=[key for regex in removeregexList for key in params.keys() if re.search(regex,key)]
        for r in removeList:
            params.pop(r)
        thisdict={}
        for peak in peaklist:
            thisdict.update(peak.row_to_dict())    
        params.update(thisdict)    

class PeakFitEditorHandler(Handler):
    
    varyList=[r'int',r'sig',r'gam']
    
#    def update_peak_list(self,dspeaks,params):
#        thisdict= dspeaks.to_dict()
#        removeregexList=[r'int',r'pos',r'sig',r'gam']
 #       removeList=[key for regex in removeregexList for key in params.keys() if re.search(regex,key)]
  #      for r in removeList:
#            params.pop(r)
 #       params.update(thisdict)    
    
    
    def close(self,info,is_ok):
        print "close the editor"
        if is_ok:
            update_peak_list(info.object.selected,info.object.selected.dataset.select_peaks_params)
        return True
               
    def do_refine(self,info):
        print 'refining...'
        update_peak_list(info.object.selected,info.object.selected.dataset.select_peaks_params)
        dataset=info.object.selected.dataset
        new_select_peaks=[]
        for pr in info.object.selected.peaks:
            if pr.fit is True:
                new_select_peaks.append(pr)  
        background,peak_profile,new_params=fit_peaks_background(new_select_peaks,self.varyList,dataset,None,dataset.select_peaks_params)
        if not hasattr(dataset,'background'):
            background_fit=dataset.copy() 
            background_fit.metadata['ui'].name = dataset.name+' fit (background)'
            background_fit.metadata['ui'].color=None  
            dataset.background=background_fit
        dataset.background.data[:,1]=background  
        dataset.select_peaks_params.update(new_params)
        # update the peaks list
        newPeaks=updatePeakRows(new_params,info.object.selected.peaks)
        #newPeaks=createPeakRows(new_params)
        info.object.selected.peaks=newPeaks
        info.object.peak_profile.data[:,1]=peak_profile
      
      
    def do_save(self,info):
        filename=info.object.selected.dataset.name.split()[0]+"_peak_data.txt"
        filename=str(get_txt_filename(filename))
        with file(filename, 'w') as outfile:
            outfile.write("Peak Fit Parameters\n")#filename.write()  
            outfile.write("Dataset name: "+info.object.selected.dataset.name+"\n")
            outfile.write("2Theta\tIntensity\tSigma\tGamma\tFWHM\n")
            for peak in info.object.selected.peaks:
                outfile.write("%4.5f\t%4.5f\t%4.5f\t%4.5f\t%4.5f\n" % (peak.position, peak.intensity, peak.sigma,peak.gamma,peak.fwhm))
        
class PeakFittingEditor(HasTraits):
    # while we store data for all the datasets that are loaded we only operate on "selected"
    # Maybe this should change so that there is only the peak list and the dataset, it would simplify things greatly.
    raw_dataset=Instance(XYEDataset)
    selected=Instance(DatasetPeaks)
    peak_profile=Instance(XYEDataset)
    index = None

    refine = Action(name = "Refine",
                action = "do_refine")
    
    save= Action(name = "Save peak list",
                action="do_save")
    
    traits_view = View(
         UItem('selected@'),
#        Item('selected@', editor=ListEditor(use_notebook=True, deletable=False, page_name='.name',selected='selected'), show_label=False),
            #VGroup(
                #Label('Modify all selected items:'),
    #            VGroup(
       #             Item('name'),
      #              Item('peaks'),
            #        springy=True
           #    ),
     #       ),
            
        
        resizable=True, width=0.5, height=0.5, kind='livemodal',
        title='Edit peaks to fit',
        handler=PeakFitEditorHandler(),
        buttons=[refine, save, OKButton,CancelButton]
               
    )
    
    
    def __init__(self, *args, **kwargs):        
        super(PeakFittingEditor, self).__init__(*args, **kwargs)
        self.selected=createDatasetPeaks(self.raw_dataset)
        #self.dataset_peaks=createDatasetPeaks(self.raw_dataset)
     #   self.selected=self.dataset_peaks
        self.peak_profile=self.selected.dataset.copy()
        self.peak_profile.name=self.selected.dataset.name+'(fitted profile)'
        self.peak_profile.metadata['ui'].name=self.selected.dataset.metadata['ui'].name+' (fitted peak profile)'
        self.peak_profile.metadata['ui'].color=None     
         
   
        
        # For now we will do only the selected dataset, the one that is the top tab that is visible see how long it takes, then loop around the other 
        # datasets if need be
        # remove peaks from fit_params if they are not ticked to refine
        # do the least squares refinement on the data with those params
        # update the display of the table. Clicking ok, "saves" the params for that dataset
        #
   
    
    
class PeakSelectorTool(LineSegmentTool):
    """
    This class extends the LineSegmentTool, we will use it for selecting peaks in the user window, not working yet
    """
    peak_list=List(PeakRowUI)
    dataset=Instance(XYEDataset)
    params={}
    callback=None
    
    def find_nearest(self,array,value):
        idx = (np.abs(array-value)).argmin()
        return array[idx]
    
    def searchOnePeak(self,position,peakNumber):
        window=0.5
        print position  
        peakrows=[]      
        while (True):
            x=self.find_nearest(self.dataset.data[:,0],position)
            xmin= x-window
            xmax=x+window
            peakrows=autosearch_peaks(self.dataset,(xmin,xmax),self.params)
            if peakrows is None or len(peakrows)>1:
                #reduce limits
                window=window/10
                if window<1e-6:
                    break
                peakrows=[]
                
            else: break
        print peakrows[0].intensity
        peakrows[0].peak_number=peakNumber
        return peakrows[0]
            
    
    def __init__(self,peak_list,dataset,callback,*args, **kwargs):        
        super(PeakSelectorTool, self).__init__(*args, **kwargs)
        self.peak_list=peak_list
        self.line.close_path=False
        self.line.line_width=0
        self.line.vertex_size=5.0
        self.dataset=dataset
        self.callback=callback
        self.params=dataset.select_peaks_params
        newpoints=[(peak.position,peak.intensity) for peak in peak_list]
        #self.selected_peaks_y=[peak.intensity for peak in peak_list]
        #self.points[:,0]=self.selected_peaks_x
        #self.points[:,1]=self.selected_peaks_y
        self.points.extend(newpoints)
        self.component.request_redraw()
   
    def _finalize_selection(self):
        peaks=[]
        iPeak=0
        for point in self.points:
            peaks.append(self.searchOnePeak(point[0],iPeak))
            iPeak+=1
        update_peak_list_by_list(peaks,self.dataset.select_peaks_params)
        self.peak_list=peaks
        self.callback(self.dataset)

   
