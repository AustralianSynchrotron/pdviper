from pathlib import Path

import numpy as np

import pytest

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


@pytest.mark.parametrize(('path', 'expected_partner_path'), [
    ('/path/foo_p1_bar', '/path/foo_p2_bar'),
    ('/path/foo_p2_bar', '/path/foo_p1_bar'),
    ('/path/foo_p3_bar', '/path/foo_p4_bar'),
    ('/path/foo_p12_bar', '/path/foo_p34_bar'),
    ('/path/foo_p34_bar', '/path/foo_p12_bar'),
    ('/path/foo_P1_bar', '/path/foo_P2_bar'),
    ('/path/foo_P2_bar', '/path/foo_P1_bar'),
    ('/path/foo_P3_bar', '/path/foo_P4_bar'),
    ('/path/foo_P12_bar', '/path/foo_P34_bar'),
    ('/path/foo_P34_bar', '/path/foo_P12_bar'),
    ('/path/foo_p_bar', None),
    ('/path/p1/foo', None),
    ('/path/p1/foo_p1_bar', '/path/p1/foo_p2_bar'),
])
def test_partner_path_handles_variations(path, expected_partner_path):
    if expected_partner_path is not None:
        expected_partner_path = Path(expected_partner_path)
    data_set = DataSet('ds1', [], [], [], path)
    assert data_set.partner_path == expected_partner_path
