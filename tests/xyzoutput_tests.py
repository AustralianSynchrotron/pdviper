import unittest
import nose
import parab
from xyzoutput import XYZGenerator
import xye
import numpy as np
from app import create_datasetui

class XYZOutputTest(unittest.TestCase):
    
    def setUp(self):
        data1=np.c_[[1,4,7],[2,5,8],[3,6,9]]
        data2=np.c_[[10,13,16,19],[11,14,18,20],[12,15,17,21]]
        xye1=xye.XYEDataset(data=data1)
        create_datasetui(xye1)
        xye1.metadata['ui'].active=True
        xye2=xye.XYEDataset(data=data2)
        create_datasetui(xye2)
        xye2.metadata['ui'].active=True
        self.datasets=[xye1,xye2]
        
    def xyzoutput_test(self):
        generator=XYZGenerator()
        xyzresult=generator.process_data(self.datasets)
        expected_result=np.array([[1,1,2],[4,1,5],[7,1,8],[10,2,11],[13,2,14],[16,2,17],[19,2,20]])
        print xyzresult
        self.assertEqual(xyzresult.all(),expected_result.all(), "Hello")
        
if __name__ == '__main__':
    nose.main()