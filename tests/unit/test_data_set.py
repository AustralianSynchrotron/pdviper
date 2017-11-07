import numpy as np

from pdviper.data_manager import DataSet

from tests.fixtures import TEST_FILE1


def test_DataSet_sets_sample_name():
    data_set = DataSet.from_xye(TEST_FILE1)
    assert data_set.name == 'file1'


def test_DataSet_attributes_supports_division():
    """ This is to ensure numpy arrays are cast as floats """
    data_set = DataSet(name='test',
                       angle=[1],
                       intensity=[1],
                       intensity_stdev=[1])
    data_set.angle /= 2
    data_set.intensity /= 2
    data_set.intensity_stdev /= 2
    assert np.array_equal(data_set.angle, np.array([.5]))
