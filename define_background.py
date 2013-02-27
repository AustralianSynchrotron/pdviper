from numpy import inf
import numpy as np
from chaco.tools.api import LineSegmentTool
from traits.api import HasTraits, Instance, Bool
from processing_background_removal import CurveFitter
from xye import XYEDataset
from copy import deepcopy

def min_max_x(datasets):
    xs=np.vstack(d.data[:,0] for d in datasets)
    min=np.min(xs)
    max=np.max(xs)
    return [min,max] 

def background_as_xye(points):
    es=np.zeros((len(points),1)) 
    return XYEDataset(data=np.hstack((np.array(points),es)))
    

def empty_xye_dataset(size):
    xs=np.linspace(size[0],size[1],10000)
    data = np.zeros((10000,3))
    data[:,0]=xs
    return XYEDataset(data=data)


class MyLineDrawer(LineSegmentTool):
    """
    This class extends the LineSegmentTool, customised the _finalize_selection routine to evaluate the fitted of the defined points on the
    dataset points.
    """
    line_points=None
    datasets=None
    plot_callback=None
    curve_fitter=None
    background_fit=None
    
    def __init__(self, *args, **kwargs):        
        super(MyLineDrawer, self).__init__(*args, **kwargs)
        self.line.close_path=False
   
    
    def attach_datasets(self,datasets):
       self.datasets=datasets
   
    def _finalize_selection(self):
        self.line.line_dash=(4.0,2.0)
        self.line_points=self.points
        xyedata= self._make_points_as_xye()
        # use the curve fitter to fit a spline to the selected points
        self.curve_fitter.fit_curve(xyedata)
        # now evaluate the spline at each of the x points for the data
        # see 
        self.background_fit.metadata=deepcopy(self.datasets[0].metadata)
        self.background_fit.data[:,1] = self.curve_fitter.eval_curve(self.background_fit.data[:,0])
        self.background_fit.metadata['ui'].name = 'fit (manual background)'        
        self.datasets.append(self.background_fit)
        self.plot_callback()


    def _make_points_as_xye(self):
        es=np.zeros((len(self.points),1))
        data1= np.hstack((np.array(self.points),es))
        dataset=XYEDataset(data=data1)
        return dataset

