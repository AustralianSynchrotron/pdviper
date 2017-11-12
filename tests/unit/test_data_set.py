from pathlib import Path

import numpy as np

import pytest

from pdviper.data_manager import DataSet, Position, CannotResolvePartner
from tests.fixtures import TEST_FILE1


def test_DataSet_sets_sample_name():
    data_set = DataSet.from_xye(TEST_FILE1)
    assert data_set.name == 'ds1_0000_p1_0000'


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
    ('/path/foo_p4_bar', '/path/foo_p3_bar'),
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
    ('/path/foo_p4_p1_bar', '/path/foo_p4_p2_bar'),
])
def test_partner_path_handles_variations(path, expected_partner_path):
    if expected_partner_path is not None:
        expected_partner_path = Path(expected_partner_path)
    data_set = DataSet(Path(path).stem, [], [], [], path)
    if expected_partner_path is not None:
        assert data_set.determine_partner_path() == expected_partner_path
    else:
        with pytest.raises(CannotResolvePartner):
            data_set.determine_partner_path()


@pytest.mark.parametrize(('path', 'expected_position'), [
    ('/path/foo', None),
    ('/path/p1/foo', None),
    ('/path/foo_p1_bar', Position.P1),
    ('/path/foo_p2_bar', Position.P2),
    ('/path/foo_p3_bar', Position.P3),
    ('/path/foo_p4_bar', Position.P4),
    ('/path/foo_p12_bar', Position.P12),
    ('/path/foo_p34_bar', Position.P34),
    ('/path/foo_P1_bar', Position.P1),
    ('/path/foo_p4_p1_bar', Position.P1),
])
def test_position_property(path, expected_position):
    data_set = DataSet(Path(path).stem, [], [], [], path)
    assert data_set.position == expected_position
