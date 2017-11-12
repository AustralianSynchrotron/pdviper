import pytest

from pdviper.data_manager import splice, DataSet
from tests.fixtures import TEST_FILE1, TEST_FILE2


def create_data_set(name, path=None):
    angle, intensity, intensity_stdev = [], [], []
    return DataSet(name=name, angle=angle, intensity=intensity,
                   intensity_stdev=intensity_stdev, path=path)


def test_splice_handles_empty_data_sets():
    ds1 = create_data_set('foo_p1_bar')
    ds2 = create_data_set('foo_p2_bar')
    result = splice([ds1, ds2])
    assert result.name == 'foo_p12_s_bar'
    assert len(result.angle) == 0


def test_splice_handles_upper_case():
    ds1 = create_data_set('foo_P1_bar')
    ds2 = create_data_set('foo_P2_bar')
    result = splice([ds1, ds2])
    assert result.name == 'foo_P12_s_bar'


def test_splice():
    ds1 = DataSet.from_xye(TEST_FILE1)
    ds2 = DataSet.from_xye(TEST_FILE2)
    ds_spliced = splice([ds1, ds2])
    assert ds_spliced.name == 'ds1_0000_p12_s_0000'


def test_splice_with_order_backwards():
    ds1 = DataSet.from_xye(TEST_FILE1)
    ds2 = DataSet.from_xye(TEST_FILE2)
    ds_spliced = splice([ds2, ds1])
    assert ds_spliced.name == 'ds1_0000_p12_s_0000'


def test_splice_handles_weird_names():
    ds1 = create_data_set('foo_bar')
    ds2 = create_data_set('foo_p2_bar')
    with pytest.raises(ValueError) as exc:
        splice([ds1, ds2])
    assert str(exc.value) == 'cannot determine position for foo_bar'


def test_splice_handles_attempts_to_splice_incompatible_positions():
    ds1 = create_data_set('foo_p1_bar')
    ds2 = create_data_set('foo_p3_bar')
    with pytest.raises(ValueError) as exc:
        splice([ds1, ds2])
    assert str(exc.value) == 'cannot splice data sets from positions 1 and 3'
