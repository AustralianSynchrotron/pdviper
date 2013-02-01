import numpy as np
from numpy import array
from copy import deepcopy
from processing import insert_descriptor
from chaco.tools.api import RangeSelection, RangeSelectionOverlay


def apply_transform(datasets,x,y,x_multiplier,y_multiplier):
    transformed_datasets=[]
    for d in datasets:
        newd=deepcopy(d)
        newd.data[:,0]=newd.data[:,0]+x
        newd.data[:,1]=newd.data[:,1]*x_multiplier+y #only makes sense to multiply y (and error in y), yes?
        newd.data[:,2]=newd.data[:,2]*y_multiplier+y
        newd.name = insert_descriptor(newd.name, 't')
        newd.metadata['ui'].name = newd.name + ' (transformed)'
        transformed_datasets.append(newd)
    return transformed_datasets    

def find_datasets_with_descriptor(datasets,descriptors):
    return [d for d in datasets if d.metadata['ui'].name==d.name+' (transformed)']

