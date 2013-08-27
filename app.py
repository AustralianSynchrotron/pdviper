import os
import re

from enable.api import ComponentEditor
from traits.api import List, Str, Float, HasTraits, Instance, Button, Enum, Bool, \
                        DelegatesTo, Range, HTML
from traitsui.api import Item, UItem, HGroup, VGroup, View, spring, Label, HSplit, Group, \
                        CheckListEditor, Tabbed, DefaultOverride, EnumEditor, HTMLEditor
                      
from pyface.api import DirectoryDialog, OK, ImageResource
from chaco.api import OverlayPlotContainer


import csv
from xye import XYEDataset
from chaco_output import PlotOutput
from raw_data_plot import RawDataPlot
from fixes import fix_background_color
from dataset_editor import DatasetEditor, DatasetUI
from wavelength_editor import WavelengthEditor, WavelengthUI
from ui_helpers import get_save_as_filename, get_save_as_csv_filename, \
    open_file_dir_with_default_handler, open_file_with_default_handler, \
    get_file_list_from_dialog, get_file_from_dialog, get_save_as_xyz_filename, get_transformed_filename,\
    get_txt_filename
import processing
from processing import DatasetProcessor
from plot_generator import PlotGenerator
from peak_fit_window import PeakFitWindow
from processing_background_removal import subtract_background_from_all_datasets, \
                                            get_subtracted_datasets, CurveFitter
from define_background import empty_xye_dataset,min_max_x
from xyzoutput import write_to_file, XYZGenerator
from transform_data import apply_transform, find_datasets_with_descriptor,dataset_already_transformed
from peak_fitting import autosearch_peaks, fit_peaks_background, createPeakRows
from peak_editor import PeakFittingEditor
from traitsui.message import message
from traitsui.editors.button_editor import ButtonEditor
import numpy
# Linux/Ubuntu themes cause the background of windows to be ugly and dark
# grey. This fixes that.
fix_background_color()


size = (1200, 700)
title = "PDViPeR"


def create_datasetui(dataset):
    ui = DatasetUI(name=dataset.name, dataset=dataset, color=None)
    dataset.metadata['ui'] = ui
    ui_w = WavelengthUI(name=dataset.name, dataset=dataset)
    dataset.metadata['ui_w'] = ui_w
    return (ui, ui_w)

class Global2(HasTraits):
    
    dataset_names=List([])

    def populate_dataset_name_list(self,datasets):
        names=set()
        for d in datasets:
            names.add(d.name)
        self.dataset_names=sorted(names)
g2 = Global2()

class Global(HasTraits):
    """
    This is just a container class for the file list so that the normalisation reference
    selector can use a drop-down list selector normally reserved by traitsui for Enum
    traits, but where we want to use a list instead and have the dropdown updated upon
    updates to the list. See discussion here describing this:
    http://enthought-dev.117412.n3.nabble.com/How-to-force-an-update-to-an-enum-list-to-propagate-td3489135.html
    """
    file_list = List([])
    
    def populate_list(self, filepaths):
        positions = set()
        for f in filepaths:
            try:
                positions.add(re.search('_(p[1-4])_', os.path.basename(f)).group(1))
            except:
                pass
        self.file_list = sorted(positions) + [os.path.basename(f) for f in filepaths]


g = Global()

  
    

class MainApp(HasTraits):
    container = Instance(OverlayPlotContainer)

    file_paths = List(Str)
    # Button group above tabbed area
    open_files = Button("Open files...")
    edit_datasets = Button("Edit datasets...")
    generate_plot = Button("Generate plot...")
    help_button = Button("Help...")
    close_files = Button("Reset data and plots")
    export_xyz = Button("Save as xyz file...")

    # View tab
    scale = Enum('linear', 'log', 'sqrt')
    options = List
    reset_button = Button("Reset view")
    copy_to_clipboard = Button("Copy to clipboard")
    save_as_image = Button("Save as image...")
    save_parabs_as_csv = Button("Save parabs as csv...")
    save_path = Str

    # Process tab
    merge_positions = Enum('all', 'p1+p2', 'p3+p4', 'p12+p34')('p1+p2')
    load_partners = Button
    splice = Bool(True)
    merge = Bool(False)
    merge_regrid = Bool(False)
    normalise = Bool(True)
    # See comment in class Global() for an explanation of the following traits
    g = Instance(Global, ())
    g2 = Instance(Global2, ())
    file_list = DelegatesTo('g')
    dataset_names=DelegatesTo('g2')
    normalisation_source_filenames = Enum(values='file_list')
    selection_dataset_names=Enum(values='dataset_names')
    def _g_default(self):
        return g
    def _g2_default(self):
        return g2
    correction = Float(0.0)
    align_positions = Bool(False)
    bt_start_peak_select = Button
    bt_end_peak_select = Button
    peak_selecting = Bool(False)

    what_to_plot = Enum('Plot new', 'Plot old and new')('Plot old and new')

    bt_process = Button("Apply")
    bt_undo_processing = Button("Undo")
    bt_save = Button("Save...")
    most_recent_path = Str('')

    # Background removal tab
    man_define_bg_button_label=Str("Define")
    bt_manually_define_background = Button('man_define_bg_button_label')
    bt_subtract_manual_background=Button("Subtract")
    bt_clear_manual_background=Button("Clear")
    background_selected= Bool(False)
    curve_order = Range(1, 1000)(3)

    curve_type=Enum('Linear Interpolation','Chebyschev Polynomial','Cosine Fourier Series')('Chebyschev Polynomial')
    bt_fit = Button("Curve fit")
    bt_save_curve=Button("Save fit params")
    bt_clear_fit=Button("Clear fit")
    bt_load_background = Button("Load...")
    bt_subtract_background = Button("Subtract background")
    bt_save_background = Button("Save...")
#    backgrounded_files = List
    background_file = None
    backgrounds_fitted=Bool(False)
    background_fits = List (XYEDataset)
    background_manual=None
    all_fit_params=List
    background_datasets=set()
    manual_bg_fitted=Bool(False)
    
    selected_dataset=Str

    # theta/d/Q tab
    filename_field = Str("d")
    bt_convertscale_abscissa = Button("Convert/scale abscissa...")

    raw_data_plot = Instance(RawDataPlot)
    fitter=None

    # rescaling 
    x_offset= Float(0.0)
    y_offset=Float(0.0)
    x_multiplier=Float(1.0)
    y_multiplier=Float(1.0)
    bt_apply_transform=Button("Apply")
    bt_save_transformed=Button("Save...")
    transform_selected_dataset=Enum(values='dataset_names')
    select_range_min=Float(0.0)
    select_range_max=Float(-1.0)
    bt_crop_range=Button("Select range")

   

    # peak fitting
    bt_autosearch_peaks=Button("Auto search peaks")
    select_peaks_button_label=Str("Select peaks")
    bt_select_peaks=Button('select_peaks_button_label')
    bt_edit_peaks=Button("Edit peaks")
    bt_plot_peak_fit=Button("Plot fitted peaks")
    bt_clear_peaks=Button("Clear peaks")
    peak_editor=None
    peak_labels=[]
    peak_select_dataset=Enum(values='dataset_names')
    bt_refine_peaks=Button("LSQ peak refinement")
    toggle_peaks_label_value=Str("Hide peak Labels")
    bt_toggle_peak_labels=Button('toggle_peaks_label_value')
    show_peak_labels=True
    peak_list=[]
    
    
    

    #-------------------------------------------------------------------------------------
    # MVC View
    view_group = VGroup(
        Label('Scale:'),
        UItem('scale', enabled_when='object._has_data()'),
        UItem('options', editor=CheckListEditor(name='_options'), style='custom', enabled_when='object._has_data()'),
        UItem('reset_button',enabled_when='object._has_data()'),
        spring,
        '_',
        spring,
        UItem('copy_to_clipboard', enabled_when='object._has_data()'),
        UItem('save_as_image', enabled_when='object._has_data()'),
        UItem('save_parabs_as_csv', enabled_when='object._has_data()'),
        label='View',
        springy=False,
    )

    process_group = VGroup(
        VGroup(
            Label('Positions to process:'),
            UItem(name='merge_positions',
                 style='custom',
                 editor=EnumEditor(values={
                     'p1+p2'   : '1: p1+p2',
                     'p3+p4'   : '2: p3+p4',
                     'p12+p34' : '3: p12+p34',
                     'all'     : '4: all',
                 }, cols=2),
                 enabled_when='object._has_data()'
            ),
            UItem('load_partners', enabled_when='object._has_data() and (object.merge_positions != "all")'),
            show_border = True,
        ),
        VGroup(
            HGroup(Item('align_positions'), enabled_when='object._has_data() and (object.merge_positions != "all")'),
            HGroup(
                UItem('bt_start_peak_select', label='Select peak',
                      enabled_when='object.align_positions and not object.peak_selecting and (object.merge_positions != "all")'),
                UItem('bt_end_peak_select', label='Align',
                      enabled_when='object.peak_selecting and (object.merge_positions != "all")'),
            ),
            Item('correction', label='Zero correction:', enabled_when='object._has_data()'),
            show_border = True,
        ),
        VGroup(
            HGroup(
                Item('splice'),
                Item('merge', enabled_when='object.merge_positions != "p12+p34"'),
                enabled_when='object._has_data() and (object.merge_positions != "all")'
            ),
            HGroup(
                Item('normalise', label='Normalise', enabled_when='object._has_data() and (object.merge_positions != "p12+p34")'),
                Item('merge_regrid', label='Grid', enabled_when='object._has_data()'),
            ),
            VGroup(
                Label('Normalise to:'),
                UItem('normalisation_source_filenames', style='simple',
                     enabled_when='object.normalise and object._has_data()'),
            ),
            show_border = True,
        ),
        spring,
        UItem('what_to_plot', editor=DefaultOverride(cols=2), style='custom',
              enabled_when='object._has_data()'),
        spring,
        UItem('bt_process', enabled_when='object._has_data()'),
        UItem('bt_undo_processing', enabled_when='object.undo_state is not None'),
        UItem('bt_save', enabled_when='object._has_data()'),
        label='Process',
        springy=False,
    )

    background_removal_group =  VGroup(
        VGroup(
            Label('Define a background curve by selecting points'),
            HGroup(               
                UItem('bt_manually_define_background', editor=ButtonEditor(label_value='object.man_define_bg_button_label'),enabled_when='object._has_data()'),
                UItem('bt_clear_manual_background', enabled_when='object._has_data() and object.manual_bg_fitted'),
            ),
            show_border = True,  
 
        ),
        VGroup(
            Label('Load from file:'),
            UItem('bt_load_background', enabled_when='object._has_data()'),
            show_border = True,
        ),
        VGroup(
            Label('Fit a background curve:'),
            UItem('selection_dataset_names',  enabled_when='object._has_data()'),
            UItem('curve_type', enabled_when='object._has_data()'),
            HGroup(
                   Item('curve_order', label='Number of Fit Parameters', enabled_when='object._has_data()'),
            ),
            HGroup(
                #spring,
                UItem('bt_fit', enabled_when='object._has_data()'),
                UItem('bt_save_curve',enabled_when='object._has_data()'),
                UItem('bt_clear_fit',enabled_when='object._has_data()'),
                #spring,
                springy=True
            ),
            show_border = True,
        ),
        UItem('bt_subtract_background', enabled_when='object._has_data() and (object.background_file!=None or object.manual_bg_fitted or object.backgrounds_fitted)'),
        UItem('bt_save_background', enabled_when='object._has_data() and object.processed_datasets!=[] and (object.background_file!=None or object.manual_bg_fitted or object.backgrounds_fitted)'),
        label='Background',
        springy=False,
    )

   
    convert_xscale_group = VGroup(   
        VGroup(                          
            Label('Filename label (prefix_<label>_nnnn.xye):'),
            UItem('filename_field',
                enabled_when='object._has_data()'),
            UItem('bt_convertscale_abscissa',
                label='Convert/scale abscissa...',
                enabled_when='object._has_data()',
                ),
            show_border=True   
        ),
        VGroup(
            Item('transform_selected_dataset',label='Dataset', enabled_when='object._has_data()'),
            VGroup(
                Label('Select Range (x) axis'),
                HGroup(
                    Item('select_range_min',label='min', enabled_when='object._has_data()'),
                    Item('select_range_max',label='max',enabled_when='object._has_data()', tooltip='-1.0 selects to the maximum x value'),
                ), 
                UItem('bt_crop_range',enabled_when='object._has_data()'),      
                show_border=True,  
            ),
            VGroup(
                Label('X and Y offsets and multipliers to rescale data'),
                HGroup(
                    Label('Offset'),
                    Item('x_offset', label='x', enabled_when='object._has_data()'),
                    Item('y_offset', label='y',enabled_when='object._has_data()'),
                ),
                HGroup(
                    Label('Multiplier'),
                    Item('x_multiplier',label='x',enabled_when='object._has_data()'),    
                    Item('y_multiplier', label='y', enabled_when='object._has_data()'),
                ),
                UItem('bt_apply_transform', enabled_when='object._has_data()'),
                show_border=True,                       
            ),
            UItem('bt_save_transformed', enabled_when='object._has_data()'),                  
            show_border=True
            ),
        label='Transforms',
        springy=True,
    )
    
    peak_fitting_group = VGroup(
        VGroup(
            Item('peak_select_dataset',label='Dataset',enabled_when='object._has_data()'),
            VGroup(
                   UItem('bt_autosearch_peaks', enabled_when='object._has_data() and object.select_peaks_button_label=="Select peaks"'), 
                   UItem('bt_select_peaks', editor=ButtonEditor(label_value='object.select_peaks_button_label'), enabled_when='object._has_data()'),
                   UItem('bt_edit_peaks', enabled_when='object.peak_editor is not None and object.peak_editor.raw_dataset.name==object.peak_select_dataset'),
                   UItem('bt_plot_peak_fit', enabled_when='object.peak_editor is not None and object.peak_editor.raw_dataset.name==object.peak_select_dataset'),
                   UItem('bt_clear_peaks',enabled_when='object.peak_editor is not None and object.peak_editor.raw_dataset.name==object.peak_select_dataset'),
                   UItem('bt_toggle_peak_labels', editor=ButtonEditor(label_value='object.toggle_peaks_label_value'), enabled_when='object.peak_editor!=None and object.peak_editor.raw_dataset.name==object.peak_select_dataset'),
                   springy=True
            ),
        ),
        label='Peak Fitting',
        springy=True,               
        show_border=True,            
    )

    traits_view = View(HSplit(
            Group(
                VGroup(
                    UItem('open_files'),
                    UItem('edit_datasets', enabled_when='object._has_data()'),
                    UItem('generate_plot', enabled_when='object._has_data()'),
                    UItem('help_button'),
                    UItem('close_files', enabled_when='object._has_data()'),
                    UItem('export_xyz', enabled_when='object._has_data()'),
                    spring,
                    spring,
                    Tabbed(
                        view_group,
                        process_group,
                        background_removal_group,
                        convert_xscale_group,
                        peak_fitting_group,
                        springy=False,
                    ),
                    show_border=False,
                ),
            ),
            Group(
                UItem('container', editor=ComponentEditor(bgcolor='white')),
                show_border=False,
                ),
            ),
            resizable=True, title=title, width=size[0], height=size[1], icon=ImageResource('pdviper_icon.ico')
        )

    #-------------------------------------------------------------------------------------
    # MVC Control
    
  
    def _has_data(self):
        return len(self.datasets) != 0

    def _reset_all(self):
        self.datasets = []
        self.dataset_pairs = set()
        self.undo_state = None
        self.file_paths = []
#        self.backgrounded_files = []
        self.processed_datasets = []
        self.background_file = None
        self.background_manual=None
        self.background_fit=None
        self.backgrounds_fitted=False
        self.bg_removed_datasets=set()
        self.background_datasets=set()
        self.peak_list=[]
        self.fitter=None
        self.raw_data_plot.reset_tools()
        if self.peak_labels is not []:
            self.raw_data_plot.remove_peak_labels(self.peak_labels)
        self.peak_labels=[]
        self.peak_editor=None

    def __init__(self, *args, **kws):
        """
        self.datasets = [ <XYEDataset>, ..., <XYEDataset> ]
        self.dataset_pairs = set([ (<XYEDataset-p1>, <XYEDataset-p2>),
                                   ...,
                                   (<XYEDataset-p1>, <XYEDataset-p2>) ])
        """
        super(MainApp, self).__init__(*args, **kws)
        self.datasets = []
        self.dataset_pairs = set()
        self.undo_state = None
        self.raw_data_plot = RawDataPlot()
        self.plot = self.raw_data_plot.get_plot()
        self.container = OverlayPlotContainer(self.plot,
            bgcolor="white", use_backbuffer=True,
            border_visible=False)
        self.pan_tool = None
        # The list of all options.
        self._options = [ 'Show legend', 'Show gridlines', 'Show crosslines' ]
        # The list of currently set options, updated by the UI.
        self.options = self._options
        self.file_paths = []
        self.processed_datasets = []
        self.background_datasets=set()
        self.bg_removed_datasets=set() # keep track of datasets where we have removed the background so we don't do it twice

    

    def _open_files_changed(self):
        file_list = get_file_list_from_dialog()
        if file_list:
            self._reset_all()
            self.most_recent_path = os.path.dirname(file_list[0])
            self.file_paths = file_list

    def _options_changed(self, opts):
        # opts just contains the keys that are true.
        # Create a dict all_options that has True/False for each item.
        all_options = dict.fromkeys(self._options, False)
        true_options = dict.fromkeys(opts, True)
        all_options.update(true_options)
        self.raw_data_plot.show_legend(all_options['Show legend'])
        self.raw_data_plot.show_grids(all_options['Show gridlines'])
        self.raw_data_plot.show_crosslines(all_options['Show crosslines'])
        self.container.request_redraw()

    def _bt_start_peak_select_changed(self):
        self.raw_data_plot.start_range_select()
        self.peak_selecting = True

    def _bt_end_peak_select_changed(self):
        self.peak_selecting = False
        selection_range = self.raw_data_plot.end_range_select()
        if not selection_range:
            return

        range_low, range_high = selection_range
        # fit the peak in all loaded dataseries
        self._get_partners()
        for datapair in self._get_dataset_pairs():
            processing.fit_peaks_for_a_dataset_pair(
                range_low, range_high, datapair, self.normalise)
        editor = PeakFitWindow(dataset_pairs=self._get_dataset_pairs(),
                               range=selection_range)
        editor.edit_traits()

    def _get_dataset_pairs(self):
        datasets_dict = dict([ (d.name, d) for d in self.datasets ])
        return [ (datasets_dict[file1], datasets_dict[file2]) \
                    for file1, file2 in self.dataset_pairs ]

    def _bt_process_changed(self):
        '''
        Button click event handler for processing. 
        '''
        # Save the unprocessed data series at this point for later undoing
        processed_datasets = []
        processor = DatasetProcessor(self.normalise, self.correction,
                                     self.align_positions,
                                     self.splice, self.merge, self.merge_regrid,
                                     self.normalisation_source_filenames,
                                     self.datasets)
        # Processing at this point depends on the "Positions to process:" radiobutton
        # selection:
        # If Splice==True, get all pairs and splice them
        # If Merge==True, get all pairs and merge them
        # If Normalise==True, always normalise
        # If Grid===True, output gridded and ungridded
        # The following processing code sould really be placed into a processor.process()
        # method, but I only worked out how to pass required stuff late in the day, so
        # I do this stuff here.
        if self.merge_positions == 'p12+p34':
            self._get_partners()        # pair up datasets corresponding to the radiobutton selection
            for dataset_pair in self._get_dataset_pairs():
                datasets = processor.splice_overlapping_datasets(dataset_pair)
                for dataset in datasets:
                    dataset.metadata['ui'].name = dataset.name + ' (processed)'
                    dataset.metadata['ui'].color = None
                processed_datasets.extend(datasets)
        elif self.merge_positions == 'all':
            # Handle "all" selection for regrid and normalise
            for d in self.datasets:
                dataset = processor.normalise_me(d)
                if dataset is not None:
                    processed_datasets.append(dataset)
                    dataset.metadata['ui'].name = dataset.name + ' (processed)'
                    dataset.metadata['ui'].color = None
                    d = dataset

                dataset = processor.regrid_me(d)
                if dataset is not None:
                    processed_datasets.append(dataset)
                    dataset.metadata['ui'].name = dataset.name + ' (processed)'
                    dataset.metadata['ui'].color = None
        else:
            self._get_partners()        # pair up datasets corresponding to the radiobutton selection
            for dataset_pair in self._get_dataset_pairs():
                datasets = processor.process_dataset_pair(dataset_pair)
                for dataset in datasets:
                    dataset.metadata['ui'].name = dataset.name + ' (processed)'
                    dataset.metadata['ui'].color = None
                processed_datasets.extend(datasets)

        self.processed_datasets = processed_datasets
        self._refresh_dataset_name_list()
        self._plot_processed_datasets()

    def _plot_processed_datasets(self):
        self._save_state()
        if 'old' in self.what_to_plot:
            datasets_to_plot = self.datasets + self.processed_datasets
        else:
            datasets_to_plot = self.processed_datasets
        self._plot_datasets(datasets_to_plot)

    def _save_state(self):
        self.undo_state = (self.datasets[:], self.dataset_pairs.copy())

    def _restore_state(self):
        if self.undo_state is not None:
            self.datasets, self.dataset_pairs = self.undo_state
            self.undo_state = None

    def _bt_undo_processing_changed(self):
        self._restore_state()
        self._refresh_dataset_name_list()
        self._plot_datasets(self.datasets)

    def _bt_save_changed(self):
        dlg = DirectoryDialog(title='Save results', default_path=self.most_recent_path)
        if dlg.open() == OK:
            self.most_recent_path = dlg.path
            for dataset in self.processed_datasets:
                filename = os.path.join(dlg.path, dataset.name)
                dataset.save(filename)
            open_file_with_default_handler(dlg.path)

    def _save_as_image_changed(self):
        if len(self.datasets) == 0:
            return
        filename = get_save_as_filename()
        if filename:
            PlotOutput.save_as_image(self.container, filename)
            open_file_dir_with_default_handler(filename)

    def _save_parabs_as_csv_changed(self):
        if len(self.datasets) == 0:
            return
        filename = get_save_as_csv_filename()
        if filename:
            with open(filename, 'wb') as csvfile:
                writer = csv.writer(csvfile, dialect='excel')
                # base the header columns on the first dataset
                columns = [c for c in self.datasets[0].metadata.keys()
                           if c not in ['ui','ui_w']]
                header_columns = sorted(columns, key=str.lower)
                writer.writerow(['filename'] + header_columns)
                # header written, now write the rows
                for d in self.datasets:
                    # Just pull out the data from the columns defined above, skipping missing data
                    row = [d.source] + [d.metadata.get(i,'') for i in header_columns]
                    writer.writerow(row)

    def _copy_to_clipboard_changed(self):
        if self.datasets:
            PlotOutput.copy_to_clipboard(self.container)

    def _scale_changed(self):
        self._plot_datasets(self.datasets)

    def _get_partner(self, position_index):
        # return index of partner; i.e., 2=>1, 1=>2, 3=>4, 4=>3, 12=>34, 34=>12
        if position_index in [1,2,3,4]:
            partner = ((position_index-1)^1)+1
        elif position_index==12:
            partner = 34
        elif position_index==34:
            partner = 12
        else:
            raise 'unparsable position'
        return partner

    def _get_position(self, filename):
        m = re.search('_p([0-9]*)_', filename)
        try:
            return int(m.group(1))
        except (AttributeError, ValueError):
            return None

    def _add_dataset_pair(self, filename):
        current_directory, filebase = os.path.split(filename)
        position_index = self._get_position(filename)
        if position_index is None:
            return

        # base filename for the associated position.
        other_filebase = re.sub('_p{}_'.format(position_index),
                                '_p{}_'.format(self._get_partner(position_index)),
                                filebase)
        other_filename = os.path.join(current_directory, other_filebase)
        if not os.path.exists(other_filename):
            return

        # OK, we've got the names and paths, now add the actual data and references.
        if other_filename not in self.file_paths:
            self._add_xye_dataset(other_filename)
            # We also need to append the new path to the file_paths List trait which is
            # already populated by the files selected using the file selection dialog
            self.file_paths.append(other_filename)
        self._refresh_normalise_to_list()

    def _bt_load_background_changed(self):
        filename = get_file_from_dialog()
        if filename is not None:
            self.background_fit = None
            self.background_file = self._add_xye_dataset(filename, container=False)
            self.background_file.metadata['ui'].name = self.background_file.name + ' (background)'
            self.background_file.metadata['ui'].color=None
            self._plot_datasets(self.datasets)
            self.background_datasets.add(self.background_file)

    def _bt_fit_changed(self):
        """
        Fits a curve of the selected type to the selected dataset. It does this by first finding the peaks in the whole dataset and fitting their 
        positions with the selected order of the curve to get an expression for the background. Background is then evaluated at the same x points
        as the dataset and a new xyedataset created for the background. Background dataset is then added to the datasets (so that it is plotted)
        and also added as an attribute to the original dataset for later use subtracting the background
        """
        #varyList=[r'Back'] #we only want to fit the background parameters here
        varyList=[]#we only want to fit the background parameters here but that is included directly in the fitting routine
        fit_params={'U':1,'V':-1,'W':0.3,'X':0,'Y':0,'backType':self.curve_type,'Back:0':1.0, 'Zero':0} # these are currently needed in the version of the routine we've modified from gsas
        # need to further think on how to get rid of them, they are just the parameters for the gaussian and lorentzian that would be used
        # to define an overall broadening of the curves due to the instrument. Qinfen says they don't want to have the overall broadening
        for i in range(1,self.curve_order):
            fit_params.update({'Back:'+str(i):0.0}) 
        dataset_to_fit=self._find_dataset_by_name(self.selection_dataset_names,self.datasets+self.processed_datasets)
        if dataset_to_fit is not None:
            dataset_to_fit.fit_params=fit_params
            dataset_to_fit.fit_params.update({'datasetName':dataset_to_fit.name})
            limits=(dataset_to_fit.data[0,0],dataset_to_fit.data[-1,0])
            peak_list=autosearch_peaks(dataset_to_fit,limits,dataset_to_fit.fit_params)
            if peak_list is None:
                message(message='Unable to fit background, try manually defining a background',title = 'Background Fit Error', buttons = [ 'OK' ], parent = None)
                peak_list=[]
                self._set_basic_fit_params(dataset_to_fit, 'fit_params') # reset the peaks parameters
                return
            background,peak_profile,new_fit_params=fit_peaks_background(peak_list,varyList,dataset_to_fit,self.background_fit,dataset_to_fit.fit_params)        
            dataset_to_fit.fit_params.update(new_fit_params)
            if hasattr(dataset_to_fit,'background'): 
                background_fit=dataset_to_fit.background  
            else:
                background_fit=dataset_to_fit.copy() 
                background_fit.metadata['ui'].name = dataset_to_fit.name+' fit (background)'
                background_fit.metadata['ui'].color=None      
            background_fit.data[:,1]=background
           
            dataset_to_fit.background=background_fit
            existing_fit=self._find_dataset_by_uiname(dataset_to_fit.name+' fit (background)', self.datasets)
            if existing_fit is not None:
                self.datasets.remove(existing_fit)
            self.datasets.append(background_fit)
            self.background_fits.append(background_fit)
            self.background_datasets.add(background_fit)
            self.backgrounds_fitted=True
            self._plot_processed_datasets()
             
    def _bt_clear_fit_changed(self):
        """
        Removes the fitted background from the selected dataset and from the plot window
        """
        d=self._find_dataset_by_name(self.selection_dataset_names,self.datasets+self.processed_datasets)
        if hasattr(d,'background') and re.search(r'fit \(background\)$',d.background.metadata['ui'].name) is not None:
            self.datasets.remove(d.background)
            self.background_datasets.remove(d.background)
            self.background_fits.remove(d.background)
            delattr(d,'background')
        self._plot_processed_datasets()
        
    def _bt_save_curve_changed(self):
        """
        Exports the fitted background parameters for the currently selected dataset to a text file.
        """
        dataset=self._find_dataset_by_name(self.selection_dataset_names,self.datasets+self.processed_datasets)
        name=dataset.name.split(".")[0]+"_background_params.txt"
        filename=str(get_txt_filename(os.path.join(self.most_recent_path,name)))
        with file(filename, 'w') as outfile:
            outfile.write("Background Parameters\n")#filename.write() 
            outfile.write("Dataset name: "+dataset.fit_params['datasetName']+"\n")
            outfile.write("Fit type: "+dataset.fit_params['backType']+"\n")
            nBak=0
            while True:
                key = 'Back:'+str(nBak)
                if key in dataset.fit_params:
                    outfile.write(key+": "+str(dataset.fit_params[key])+"\n")
                    nBak+= 1
                else:
                    break


    def _bt_subtract_background_changed(self):
        """
        Triggers the background subtraction. If there are processed datasets then we subtract the background from that, otherwise we subtract
        the background from the raw dataset. We pass all the different kinds of background that could be defined and work out the logic in the
        subtract_background... method
        """
        pdata_as_set=set(self.processed_datasets)
        if len(pdata_as_set-self.bg_removed_datasets)>0: # need to check for datasets with background already subtracted
            processed_datasets = subtract_background_from_all_datasets(pdata_as_set-self.bg_removed_datasets, self.background_file, self.background_manual,self.fitter)
        else:
            processed_datasets = subtract_background_from_all_datasets(self.datasets, self.background_file, self.background_manual,self.fitter)
        if self.raw_data_plot.line_tool is not None:
            self.raw_data_plot.remove_line_tool()
        for pd in processed_datasets:
            self.bg_removed_datasets.add(pd)
        self.processed_datasets.extend(processed_datasets)
        self._plot_processed_datasets()
        self._refresh_dataset_name_list()
        
    def _bt_save_background_changed(self):
        """
        Outputs the fitted background parameters to a file.
        """
        wildcard = 'All files (*.*)|*.*'
        dlg = DirectoryDialog(title='Save results', default_path=self.most_recent_path)
        if dlg.open() == OK:
            self.most_recent_path = dlg.path
            for dataset in self.processed_datasets:
                filename = os.path.join(dlg.path, dataset.name)
                dataset.save(filename)
            open_file_with_default_handler(dlg.path)

    def _fit_manual_background_callback(self):
        self.man_define_bg_button_label="Define"
        self.manual_bg_fitted=True
        self._plot_processed_datasets()
        self.raw_data_plot.remove_tooltips('line_drawer_tool')
        self.raw_data_plot.plot.overlays.remove(self.raw_data_plot.line_tool)        
        self.raw_data_plot.zoom_tool.drag_button="left"
        self.container.request_redraw()

    def _bt_manually_define_background_changed(self):        
        """
            When the define button is clicked, this function attaches a line-drawing tool to the plot to select points to define a background.
            The _plot_processed_datasets routine is passed as a parameter so that it can be called when the points are finalised which is done 
            in the MyLineDrawer class extending the line drawing tool
        """
        if self.man_define_bg_button_label=="Define":
            man_bg=self._manual_background_fitted()
            if man_bg: 
                self.datasets.remove(man_bg)
                self._plot_processed_datasets()
            self.background_manual=empty_xye_dataset(size=min_max_x(self.datasets))
            create_datasetui(self.background_manual)
            self.fitter = CurveFitter(curve_type='Spline', deg=self.curve_order)
            self.raw_data_plot.add_line_drawer(self.datasets,self.fitter,self._fit_manual_background_callback,self.background_manual)
            self.man_define_bg_button_label="Cancel"
            self.container.request_redraw()
            self.background_datasets.add(self.background_manual)
        elif self.man_define_bg_button_label=="Cancel":
            self.raw_data_plot.remove_line_tool()
            self.fitter=None
            self.background_manual=None
            self.man_define_bg_button_label="Define"
            self.container.request_redraw()
                        
    def _manual_background_fitted(self):
        return self._find_dataset_by_uiname('fit (manual background)', self.datasets)
        
    def _bt_clear_manual_background_changed(self):
        """
        Removes the background dataset created from the manually defined, spline fitted background
        """
        if self.background_manual:
            self.datasets.remove(self.background_manual)
            self.background_datasets.remove(self.background_manual)
        self.fitter=None
        self.background_manual=None
        self.manual_bg_fitted=False
        for d in get_subtracted_datasets(self.processed_datasets):
            self.processed_datasets.remove(d)
        self.raw_data_plot.remove_line_tool()
        self._plot_processed_datasets()
        self._refresh_dataset_name_list()
        
        
    def _get_partners(self):
        """
        Populates the self.dataset_pairs list with all dataset partners in
        self.file_paths corresponding to the merge_positions radiobutton selection.
        """
        matching_re = {'all':    ''            ,
                       'p1+p2':  '_p[12]_'     ,
                       'p3+p4':  '_p[34]_'     ,
                       'p12+p34':'_p(?:12|34)_',
                      }
        basenames = [os.path.basename(f) for f in self.file_paths]
        filtered_paths = [f for f in basenames if re.search(matching_re[self.merge_positions], f) is not None]
        self.dataset_pairs = set()
        for filebase in filtered_paths:
            # base filename for the first position.
            position_index = self._get_position(filebase)
            if position_index is None:
                return
            other_filebase = re.sub('_p{}_'.format(position_index),
                                    '_p{}_'.format(self._get_partner(position_index)),
                                    filebase)
            if filebase in basenames and other_filebase in basenames:
                if position_index!=12 and (position_index&1)==0:
                    self.dataset_pairs.add((other_filebase, filebase))
                else:
                    self.dataset_pairs.add((filebase, other_filebase))
        return self.dataset_pairs

    def _refresh_dataset_name_list(self):
        #add the processed but not the backgrounded
        dataset_set=set(self.datasets+self.processed_datasets)-self.background_datasets
        g2.populate_dataset_name_list(list(dataset_set))

    def _refresh_normalise_to_list(self):
        g.populate_list(self.file_paths)

    def _file_paths_changed(self, new):
        """
        When the file dialog box is closed with a selection of filenames,
        just generate a list of all the filenames
        """
        self.datasets = []
        # self.file_paths is modified by _add_dataset_pair() so iterate over a copy of it.
        for filename in self.file_paths[:]:
            self._add_xye_dataset(filename)
        self._plot_datasets(self.datasets)
        self.datasets.sort(key=lambda d: d.name)
        self._refresh_normalise_to_list()
        self._refresh_dataset_name_list()

    def _load_partners_changed(self):
        for filename in self.file_paths[:]:
            self._add_dataset_pair(filename)
        self._plot_datasets(self.datasets)
        self.datasets.sort(key=lambda d: d.name)
        self._refresh_dataset_name_list()

    def _plot_datasets(self, datasets, reset_view=True):
        datasets_to_plot = datasets[:]
        if self.background_file is not None:
            datasets_to_plot.append(self.background_file)
        self.raw_data_plot.plot_datasets(datasets_to_plot, scale=self.scale,
                                         reset_view=reset_view)
        self._options_changed(self.options)
        self.container.request_redraw()

    def _edit_datasets_changed(self):
        editor = DatasetEditor(datasets=self.datasets)
        editor.edit_traits()
        if self._plot_datasets(self.datasets, reset_view=False) is None:
            self.raw_data_plot.remove_peak_labels(self.peak_labels)

    def _generate_plot_changed(self):
        if self.datasets:
            datasets=list(set(self.datasets)-self.background_datasets)
            datasets.sort(key=lambda d: d.name)
            generator = PlotGenerator(datasets=datasets)
            generator.show()

    def _help_button_changed(self):
        help_box = HelpBox()
        help_box.edit_traits()

    def _reset_button_changed(self):
        self.raw_data_plot.reset_view()

    def _add_xye_dataset(self, file_path, container=True):
        try:
            dataset = XYEDataset.from_file(file_path)
        except IOError:
            return
        if container:
            self.datasets.append(dataset)
        create_datasetui(dataset)
        return dataset

    def _bt_convertscale_abscissa_changed(self):
        editor = WavelengthEditor(datasets=self.datasets, filename_field=self.filename_field)
        editor.edit_traits()
        self._plot_datasets(self.datasets, reset_view=False)

    def _close_files_changed(self):
        """
        Removes all current files and processing and resets the plot display
        """
        self._reset_all()
        self.plot.x_axis.invalidate()
        self.plot.y_axis.invalidate()
        self.container.request_redraw()
      
    def _export_xyz_changed(self):
        """
        Exports the current datasets to an xyz file. Excludes background datasets.
        """
        xyzgen=XYZGenerator()
        datasets=list(set(self.datasets)-self.background_datasets)
        datasets.sort(key=lambda d: d.name)
        xyzdata=xyzgen.process_data(datasets=datasets)
        defaultfilename=os.path.basename(self.file_paths[0])
        defaultfilename=re.sub(r"_p[0-9]*[_nsmbgt]*_\d{4}.xye?",".xyz",defaultfilename)
        filename=get_save_as_xyz_filename(directory=self.most_recent_path,filename=defaultfilename)
        if filename is not None:
            write_to_file(filename,xyzdata)
            #for i in range(len(xyzdata)):
            #    f.write('{0:f}\t{1:f}\t{2:f}\n'.format(xyzdata[i,0], xyzdata[i,1], xyzdata[i,2]))
    
    def _find_dataset_by_name(self,name,datasets): 
            xs=[x for x in datasets if name==x.name]
            return xs[0] if len(xs)>0 else None       
    
    def _find_dataset_by_uiname(self,name,datasets): 
            xs=[x for x in datasets if name==x.metadata['ui'].name]
            return xs[0] if len(xs)>0 else None       
    
    def _bt_apply_transform_changed(self):
        """
        Applies a transform to all the selected dataset.
        """                    
        dataset=self._find_dataset_by_name(self.transform_selected_dataset,self.datasets+self.processed_datasets)
        scaled_datasets=apply_transform(datasets=[dataset], x=self.x_offset,y=self.y_offset,
                                        x_multiplier=self.x_multiplier, y_multiplier=self.y_multiplier)
        for d in scaled_datasets:
            #check the this dataset is not already in processed datasets so t
            td=self._find_dataset_by_name(d.name,self.processed_datasets)
            if td is not None:
                self.processed_datasets.remove(td)
            d.metadata['ui'].color=None
            self.processed_datasets.append(d)
                                
        self._plot_processed_datasets()

    def _bt_crop_range_changed(self):
        """
        Crops dataset to within the range specified.
        """
        dataset=self._find_dataset_by_name(self.transform_selected_dataset,self.datasets+self.processed_datasets)
        tdataset=dataset_already_transformed(dataset,self.processed_datasets)
        if tdataset is None:
            cropped_dataset=dataset.copy()
            cropped_dataset.metadata['ui'].color=None
            cropped_dataset.name = processing.insert_descriptor(cropped_dataset.name, 't')
            cropped_dataset.metadata['ui'].name = cropped_dataset.name + ' (transformed)'
            self.processed_datasets.append(cropped_dataset)
        elif tdataset is not None and (self.select_range_max>max(tdataset.data[:,0]) or self.select_range_min<min(tdataset.data[:,0])):
            cropped_dataset=tdataset
            cropped_dataset.data=dataset.data
        else:
            cropped_dataset=tdataset
        cropped_indices=numpy.where(cropped_dataset.data[:,0]>self.select_range_min)[0]
        if self.select_range_max!=-1.0:
            cropped_indices2=numpy.where(cropped_dataset.data[:,0]<self.select_range_max)[0]
            cropped_indices=numpy.intersect1d(cropped_indices, cropped_indices2)
        #  cropped_data=numpy.where(cropped_data<self.select_range_max)
        
        newdata=cropped_dataset.data[cropped_indices[0]:numpy.max(cropped_indices)]
        cropped_dataset.data=newdata
        self._refresh_dataset_name_list()
        self._plot_processed_datasets()


    def _bt_save_transformed_changed(self):
        """
        Saves transformed datasets to an xye file
        """
        transformed_datasets=find_datasets_with_descriptor(datasets=self.processed_datasets,descriptors='t')
        for d in transformed_datasets:
            filename=os.path.join(self.most_recent_path,d.name)
            filename=get_transformed_filename(filename)
            if filename:
                d.save(filename)
 
    
    def _set_basic_fit_params(self,dataset,property_name):
        """
        Sets up a dictionary of the basic parameters required for the background curve fitting and peak fitting routines. The property_name 
        attribute sets whether it is for background peak fitting.
        """
        params={'U':1,'V':-1,'W':0.3,'X':0,'Y':0,'Zero':0,'backType':self.curve_type,'Back:0':1.0, 'datasetName':dataset.name} 
        for i in range(1,self.curve_order):
            params.update({'Back:'+str(i):0.0}) 
        setattr(dataset,property_name,params)
    
    def _bt_autosearch_peaks_changed(self):
        """
        Searches for peak positions using a routine adapted from GSASII, does a basic fit of the peak positions only with the background 
        the form of which is specified in curve fit section of the the background tab. Currently we cannot use a manually defined background spline
        or an uploaded background file when fitting peaks. You can, however, select a dataset which has had one of these backgrounds already subtracted
        and the background curve which is then fitted should have minimal impact on the peaks.
        """
        varyList=[]
        #varyList=[r'Back']
        dataset=self._find_dataset_by_name(self.peak_select_dataset,self.datasets+self.processed_datasets)
        self._set_basic_fit_params(dataset,'select_peaks_params')
        # for d in datasets:
        limits=(dataset.data[0,0],dataset.data[-1,0])
        peak_list=autosearch_peaks(dataset,limits,dataset.select_peaks_params)
        if peak_list is None:
            message(message='Unable to find and fit peaks,\n try selecting peaks manually',title = 'Peak Search Error', buttons = [ 'OK' ], parent = None)
            peak_list=[]
            self._set_basic_fit_params(dataset, 'select_peaks_params') # reset the peaks parameters
            return
        background,peak_profile,new_fit_params=fit_peaks_background(peak_list,varyList,dataset,self.background_file,dataset.select_peaks_params)
        #need to update the background if we used the background fit
        dataset.select_peaks_params=new_fit_params.copy()
        dataset.select_peaks_params.update({'datasetName':dataset.name})
    #    editor = PeakFittingEditor(datasets=datasets)
        self.peak_editor=PeakFittingEditor(raw_dataset=dataset)
        self.peak_editor.edit_traits()        
        self.peak_labels=self.raw_data_plot.update_peak_labels(self.peak_labels,self.peak_editor.selected.peaks,self.peak_editor.peak_profile)
        self.show_peak_labels=True  
        self.toggle_peaks_label_value="Hide Peak Labels"
        self._plot_processed_datasets()

    def _bt_edit_peaks_changed(self):
        """
        Opens the peak editor window so that peak parameters can be manipulated either directly or by doing a least squares refinement
        """
        self.peak_editor.edit_traits()
        self.peak_labels=self.raw_data_plot.update_peak_labels(self.peak_labels,self.peak_editor.selected.peaks,self.peak_editor.peak_profile)
        self.show_peak_labels=True
        self.toggle_peaks_label_value="Hide Peak Labels"
        self._plot_datasets(self.datasets, reset_view=False)
        
    def _bt_plot_peak_fit_changed(self):
        """
        Plots the profile of the fitted peaks
        """
        peak_profile_dataset=self.peak_editor.peak_profile
        self.processed_datasets.append(peak_profile_dataset)
        self._plot_processed_datasets()

    def _peak_select_callback(self,dataset):
        # this function is passed to the peak selector tool and is called in the finalise_selection method.
        # it allows us to remove the selector tool, turn the points into peaks and create labels on hitting enter after
        # picking some points for peaks
        if self.peak_editor is None:
            self.peak_editor = PeakFittingEditor(raw_dataset=dataset)
        self.peak_editor.selected.peaks=self.raw_data_plot.peak_selector_tool.peak_list
        self.peak_editor.edit_traits()
        self.peak_labels=self.raw_data_plot.update_peak_labels(self.peak_labels,self.peak_editor.selected.peaks,self.peak_editor.peak_profile)
        self.show_peak_labels=True
        self.toggle_peaks_label_value="Hide Peak Labels"
        self.raw_data_plot.remove_peak_selector()
        self.select_peaks_button_label="Select peaks"
        self.raw_data_plot.remove_tooltips('peak_selector')
        self._plot_processed_datasets()

    def _bt_select_peaks_changed(self):
        """
        This button allows for peaks to be selected at the positions given by the user, and fits the height, sigma etc.
        Operates only on the one dataset which is currently selected.
        """        
        dataset=self._find_dataset_by_name(self.peak_select_dataset,self.datasets+self.processed_datasets)
        
        if self.select_peaks_button_label=="Select peaks":
            if not hasattr(dataset,'select_peaks_params'):           
                self._set_basic_fit_params(dataset,'select_peaks_params')
            self.peak_list=createPeakRows(dataset.select_peaks_params)                    
            self.raw_data_plot.add_peak_selector(self.peak_list,dataset,self._peak_select_callback)
            self.select_peaks_button_label="Cancel peak selection"
            self.container.request_redraw()
        elif self.select_peaks_button_label=="Cancel peak selection":
            self.raw_data_plot.remove_peak_selector() # remove selector tool
            self.select_peaks_button_label="Select peaks"
            self.container.request_redraw()

    def _bt_clear_peaks_changed(self):
        """
        Clears all peaks for the dataset
        """
        dataset=self._find_dataset_by_name(self.peak_select_dataset,self.datasets+self.processed_datasets)
        if hasattr(dataset,'select_peaks_params'):
            delattr(dataset,'select_peaks_params')
            #dataset.select_peaks_params=None
            self.peak_list=[]
            self.raw_data_plot.remove_peak_labels(self.peak_labels)
            self.peak_labels=[]
            self.peak_editor=None
            peakfitdataset=self._find_dataset_by_uiname(dataset.metadata['ui'].name+' (fitted peak profile)',self.datasets+self.processed_datasets)
            if peakfitdataset:
                self.processed_datasets.remove(peakfitdataset)
            # remove peak fit dataset
        self._plot_processed_datasets()

    def _bt_toggle_peak_labels_fired(self):
        """
        Removes or adds the peak labels from view but doesn't 
        """
        if self.show_peak_labels:
            self.raw_data_plot.remove_peak_labels(self.peak_labels)
            self.show_peak_labels=False
            self.peak_labels=[]
            self.toggle_peaks_label_value="Show peak Labels"
        else:
            self.peak_labels=self.raw_data_plot.update_peak_labels(self.peak_labels, self.peak_editor.selected.peaks)
            self.show_peak_labels=True
            self.toggle_peaks_label_value="Hide Peak Labels"
    

class HelpBox(HasTraits):
    help_text = HTML

    traits_view = View(
        UItem('help_text', editor=HTMLEditor(format_text=True)),
        title='Help',
        kind='modal',
        resizable=True,
        height = 600, width=800,
        buttons = ['OK'],
    )

    def __init__(self, *args, **kws):
        super(HelpBox, self).__init__(*args, **kws)
        self.help_text = \
"""
<h5>Plot region usage</h5>
Left drag = Zoom a selection of the plot <br>
Left double click = Reset to the original plot view <br>
Right drag = Pan the plot <br>
Right click = Undo zoom <br>
Esc = Reset zoom/pan <br>
Mousewheel = Zoom in/out <br>

For further help refer to the PDViPer manual located at:
<a href="http://pdviper.readthedocs.org"/>http://pdviper.readthedocs.org</a> <br>


<h5>About the software</h5>
Please send bug reports and suggestions to <br>
<a href="mailto:pdviper@synchrotron.org.au">pdviper@synchrotron.org.au</a> <br>

Software authors: <br>
Lenneke Jong, Australian Synchrotron, <a href="mailto:lenneke.jong@synchrotron.org.au">lenneke.jong@synchrotron.org.au</a><br>
Gary Ruben, Victorian eResearch Strategic Initiative (VeRSI), <a href="mailto:gruben@versi.edu.au">gruben@versi.edu.au</a> <br>
Kieran Spear, VeRSI, <a href="mailto:kieran.spier@versi.edu.au">kieran.spier@versi.edu.au</a> <br>
<a href="http://www.versi.edu.au">http://www.versi.edu.au</a> <br>

Software home: <br>
<a href="http://www.synchrotron.org.au/pdviper">http://www.synchrotron.org.au/pdviper</a> <br>
Software source: <br>
<a href="http://github.com/AustralianSynchrotron/pdviper">http://github.com/AustralianSynchrotron/pdviper</a> <br>

Recognition of NeCTAR funding:
The Australian Synchrotron is proud to be in partnership with the National eResearch
Collaboration Tools and Resources (NeCTAR) project to develop eResearch Tools for the
synchrotron research community. This will enable our scientific users to have instant
access to the results of data during the course of their experiment which will
facilitate better decision making and also provide the opportunity for ongoing data
analysis via remote access.<br>

Copyright (c) 2013, Synchrotron Light Source Australia Pty Ltd <br>
All rights reserved.
"""


def main():
    demo = MainApp()
    demo.configure_traits()

if __name__ == "__main__":
    main()
