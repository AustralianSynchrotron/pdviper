import numpy as np
from numpy import linspace, meshgrid
from numpy import array
from xye import XYEDataset
from scipy import interpolate


def cubic_interpolate(x, y, z, x_size, y_size):
    xsi = linspace(np.min(x), np.max(x), x_size)
    ysi = linspace(1, y.shape[0], y_size)
    xi, yi = meshgrid(xsi, ysi)
    zi = interpolate.griddata((x.ravel(), y.ravel()), z.ravel(), (xi, yi), method='cubic')
    return xi, yi, zi


def bin_data(data, num_bins):
    binned_y = []
    x = data[:,:,0]
    xs = linspace(np.min(x), np.max(x), num_bins + 1)
    # Make sure the maximum point falls inside the last bin
    xs[-1] += 1
    for dataset in data:
        x, y = dataset.T
        bin_indexes = np.digitize(x, xs)
        binned_y.append([ y[bin_indexes == i] for i in range(1, len(xs)) ])

    max_y = np.vstack([ array([ bin.max() if len(bin) > 0 else 0.0 for bin in y ]) for y in binned_y ])
    xsb = linspace(np.min(x), np.max(x), num_bins)
    ysb = linspace(1, max_y.shape[0], max_y.shape[0])
    x, y = meshgrid(xsb, ysb)
    return x, y, max_y


def stack_datasets(datasets):
    #normalise_datasets(datasets)
    shapes = [ len(dataset.data) for name, dataset in datasets.iteritems() ]
    min_x_len = np.min(shapes)
    data = [ dataset.data[:min_x_len] for name, dataset in datasets.iteritems() ]
    stack = np.vstack([data])
    return stack


def interpolate_datasets(datasets, points):
    x = datasets[:,:,0]
    y = datasets[:,:,1]
    x_min = x.min(axis=1).max()
    x_max = x.max(axis=1).min()
    x_index = np.linspace(x_min, x_max, points)
    y_data = None
    for x_row, y_row in zip(x, y):
        tck = interpolate.splrep(x_row, y_row, s=0, k=3)
        y_new = interpolate.splev(x_index, tck, der=0)
        if y_data is None:
            y_data = array([y_new])
        else:
            y_data = np.vstack([y_data , y_new])
    return (x_index, y_data)


def rescale(data, method='log'):
    if method == 'log':
        new_data = np.log(data)
    elif method == 'sqrt':
        new_data = np.sqrt(data)
    else:
        new_data = data
    return new_data


def fill_gaps(dataset, method='merge'):
    filename = dataset.source
    if '_p1_' not in filename:
        return dataset.data
    p2_filename = filename.replace('_p1_', '_p2_')
    try:
        disabled
        p2 = XYEDataset.from_file(p2_filename)
        key = 'Integrated Ion Chamber Count(counts)'
        p2_count = p2.metadata[key]
        p1_count = dataset.metadata[key]
        p2.data[:,1] *= p1_count / p2_count
        dataset.data = combine_by_merge(dataset, p2)
    except:
        pass
    return dataset.data


def combine_by_merge(d1, d2):
    combined = np.vstack([d1.data, d2.data])
    indices = combined[:,0].argsort()
    new_data = combined[indices]
    x, y = np.transpose(new_data)
    # Remove duplicate x values that interfere with interpolation
    x_diff = np.diff(x)
    # Don't forget the first element, which doesn't have a diff result yet
    x_diff = np.r_[1, x_diff]
    # Only take the unique values from the array
    x_uniq = x_diff > 0
    return new_data[x_uniq]


def normalise_datasets(datasets):
    key = 'Integrated Ion Chamber Count(counts)'
    counts = array([ dataset.metadata[key] for dataset in datasets.values() ])
    max_count = counts.max()
    for dataset in datasets.values():
        dataset.data[:,1] *= max_count / dataset.metadata[key]


