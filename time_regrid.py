import cProfile
import numpy as np
import processing as p
import matplotlib.pyplot as plt

data = np.load('data.npy')
cProfile.run('p.regrid_data(data)')

data2 = p.regrid_data(data, start=.5, interval=.06)
data2 = np.clip(data2, -1000,1000)
plt.plot(data[:,0], data[:,1], 'r-', data2[:,0], data2[:,1], 'b-')
plt.show()