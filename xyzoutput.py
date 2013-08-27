import numpy as np
from processing import stack_datasets

def write_to_file(filename,xyzdata):
    with file(filename, 'w') as outfile:
        outfile.write("2Theta(X)\tDataset(Y)\tIntensity(Z)\n")
        np.savetxt(outfile,xyzdata,fmt='%4.5f\t%2.1f\t%10.5f',delimiter='\t',newline='\n')

class XYZGenerator():


    def process_data(self, datasets):
        data=[ dataset.data[:len(dataset.data)] for dataset in datasets if dataset.metadata['ui'].active ]
        print data
        stack = np.vstack(data)

        xs = stack[:,0]
        zs=stack[:,1]
        
        ys=np.concatenate([ np.array([i]*data[i-1].shape[0]) for i in range(1, len(datasets) + 1) ])
               
        xyzdata=np.zeros((len(xs.flat),3),float)
        for i in range(len(xs)):
            xyzdata[i]=np.array([xs[i],ys[i],zs[i]])
       
        return xyzdata
    
