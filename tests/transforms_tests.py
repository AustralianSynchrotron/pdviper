import unittest
import numpy as np
import nose

from transform_data import apply_transform
import xye

from app import create_datasetui

class TransformDataTest(unittest.TestCase):
    
    def setUp(self):
        data1=np.c_[[1,4,7],[2,5,8],[3,6,9]]
        data2=np.c_[[10,13,16,19],[11,14,18,20],[12,15,17,21]]
        xye1=xye.XYEDataset(data=data1,name='test_data_0001.xye')
        create_datasetui(xye1)
        xye1.metadata['ui'].active=True
        xye2=xye.XYEDataset(data=data2,name='test_data_0002.xye')
        create_datasetui(xye2)
        xye2.metadata['ui'].active=True
        self.datasets=[xye1,xye2]
    
    def offset_test(self):
        x1=15
        y1=0
        x2=0
        y2=1000
        x_multiplier=1
        y_multiplier=1
        transformed1=apply_transform(self.datasets,x1,y1,x_multiplier,y_multiplier)
        transformed2=apply_transform(self.datasets,x2,y2,x_multiplier,y_multiplier)
        expected1=np.c_[[16,19,22],[2,5,8],[3,6,9]]
        expected2=np.c_[[10,13,16,19],[11,14,18,20],[12,15,17,21]]
        expected3=np.c_[[1,4,7],[1002,1005,1008],[3,6,9]]
        expected4=np.c_[[10,13,16,19],[1011,1014,1018,1020],[12,15,17,21]]
        self.assertEqual(expected1.all(),transformed1[0].data.all(),"Fail")
        self.assertEqual(expected2.all(),transformed1[1].data.all(),"Fail")
        self.assertEqual(expected3.all(),transformed2[0].data.all(),"Fail")
        self.assertEqual(expected4.all(),transformed2[1].data.all(),"Fail")
    
    def multiplier_test(self):
        x=0
        y=0
        x_multiplier1=10
        y_multiplier1=1
        x_multiplier2=1
        y_multiplier2=10
        transformed1=apply_transform(self.datasets,x,y,x_multiplier1,y_multiplier1)
        transformed2=apply_transform(self.datasets,x,y,x_multiplier2,y_multiplier2)
        expected1=np.c_[[10,40,70],[2,5,8],[3,6,9]]
        expected2=np.c_[[100,130,160,190],[11,14,18,20],[12,15,17,21]]
        expected3=np.c_[[1,4,7],[20,50,80],[3,6,9]]
        expected4=np.c_[[10,13,16,19],[110,140,180,200],[12,15,17,21]]
        self.assertEqual(expected1.all(),transformed1[0].data.all(),"Fail")
        self.assertEqual(expected2.all(),transformed1[1].data.all(),"Fail")
        self.assertEqual(expected3.all(),transformed2[0].data.all(),"Fail")
        self.assertEqual(expected4.all(),transformed2[1].data.all(),"Fail")
    
        
    def combined_test(self):
        x1=10
        y1=1000
        x2=20
        y2=2000
        x_multiplier1=2
        y_multiplier1=10
        x_multiplier2=5
        y_multiplier2=20
        transformed1=apply_transform(self.datasets,x1,y1,x_multiplier1,y_multiplier1)
        transformed2=apply_transform(self.datasets,x2,y2,x_multiplier2,y_multiplier2)
        expected1=np.c_[[10,40,70],[2,5,8],[3,6,9]]
        expected2=np.c_[[100,130,160,190],[11,14,18,20],[12,15,17,21]]
        expected3=np.c_[[1,4,7],[20,50,80],[3,6,9]]
        expected4=np.c_[[10,13,16,19],[110,140,180,200],[12,15,17,21]]
        self.assertEqual(expected1.all(),transformed1[0].data.all(),"Fail")
        self.assertEqual(expected2.all(),transformed1[1].data.all(),"Fail")
        self.assertEqual(expected3.all(),transformed2[0].data.all(),"Fail")
        self.assertEqual(expected4.all(),transformed2[1].data.all(),"Fail")
    
    
if __name__ == '__main__':
    nose.main()