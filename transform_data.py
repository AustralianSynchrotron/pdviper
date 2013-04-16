import re
from copy import deepcopy
from processing import insert_descriptor


def apply_transform(datasets,x,y,x_multiplier,y_multiplier):
    transformed_datasets=[]
    for d in datasets:
        name=re.search("(transformed)",d.metadata['ui'].name) 
        if name is None:
            newd=deepcopy(d)
            newd.data[:,0]=newd.data[:,0]*x_multiplier+x
            newd.data[:,1]=newd.data[:,1]*y_multiplier+y 
            newd.data[:,2]=newd.data[:,2]*y_multiplier+y
            newd.name = insert_descriptor(newd.name, 't')
            newd.metadata['ui'].name = newd.name + ' (transformed)'
            transformed_datasets.append(newd)
    return transformed_datasets    

def find_datasets_with_descriptor(datasets,descriptors):
    return [d for d in datasets if d.metadata['ui'].name==d.name+' (transformed)']

def dataset_already_transformed(dataset,transformed_datasets):
    td=[d for d in transformed_datasets if d.metadata['ui'].name==d.name+' (transformed)']
    if len(td)>0:
        return td[0]
    else:
        return None