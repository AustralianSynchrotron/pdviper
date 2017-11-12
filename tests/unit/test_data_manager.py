from unittest.mock import Mock, call
from pathlib import Path

import numpy as np

import pytest

from tests.fixtures import (TEST_FILE1, TEST_FILE2, P1_ARRAY, P2_ARRAY,
                            P12_SPLICE_MERGED_ARRAY)

from pdviper.data_manager import DataManager, DataSet, MergePartners


def create_data_set(name, path=None, array=None):
    if array is None:
        angle, intensity, intensity_stdev = [], [], []
    else:
        angle, intensity, intensity_stdev = array.T
    return DataSet(name=name, angle=angle, intensity=intensity,
                   intensity_stdev=intensity_stdev, path=path)


@pytest.fixture
def manager():
    yield DataManager()


def test_load_handles_no_paths(manager):
    observer = Mock()
    manager.add_observer(observer)
    manager.load([])
    assert observer.data_sets_added.called is False


def test_load_handles_invalid_paths(manager):
    observer = Mock()
    manager.add_observer(observer)
    manager.load([Path('/bad/path')])
    assert observer.data_sets_added.called is False


def test_data_manager_loads_str_and_Path_types(manager):
    manager.load([str(TEST_FILE1), Path(TEST_FILE2)])


def test_data_manager_doesnt_load_file_twice(manager):
    manager.load([TEST_FILE1])
    manager.load([TEST_FILE1])
    assert len(manager.data_sets) == 1


def test_data_manager_adds_observers(manager):
    observer1 = Mock()
    observer2 = Mock()
    manager.add_observer(observer1)
    manager.add_observer(observer2)
    manager.load([TEST_FILE1])
    assert observer1.data_sets_added.call_args == call([0])
    assert observer2.data_sets_added.call_args == call([0])


def test_data_manager_removes_observers(manager):
    observer1 = Mock()
    observer2 = Mock()
    manager.add_observer(observer1)
    manager.add_observer(observer2)
    manager.remove_observer(observer1)
    manager.load([TEST_FILE1])
    assert observer1.data_sets_added.called is False
    assert observer2.data_sets_added.called is True


def test_data_manager_removes_a_data_set(manager):
    manager.data_sets.extend([
        create_data_set('ds1'),
        create_data_set('ds2'),
        create_data_set('ds3'),
    ])
    manager.remove([1])
    assert len(manager.data_sets) == 2
    assert manager.data_sets[0].name == 'ds1'
    assert manager.data_sets[1].name == 'ds3'


def test_data_manager_removes_multiple_data_sets(manager):
    manager.data_sets.extend([
        create_data_set('ds1'),
        create_data_set('ds2'),
        create_data_set('ds3'),
        create_data_set('ds4'),
    ])
    manager.remove([1, 2])
    assert len(manager.data_sets) == 2
    assert manager.data_sets[0].name == 'ds1'
    assert manager.data_sets[1].name == 'ds4'


def test_data_manager_removes_multiple_data_sets_when_indexes_out_of_order(manager):
    manager.data_sets.extend([
        create_data_set('ds1'),
        create_data_set('ds2'),
        create_data_set('ds3'),
        create_data_set('ds4'),
    ])
    manager.remove([2, 1])
    assert len(manager.data_sets) == 2
    assert manager.data_sets[0].name == 'ds1'
    assert manager.data_sets[1].name == 'ds4'


def test_data_manager_notifies_observers_on_removal(manager):
    manager.data_sets.extend([create_data_set('ds1'), create_data_set('ds2')])
    observer1, observer2 = Mock(), Mock()
    manager.add_observer(observer1)
    manager.add_observer(observer2)
    manager.remove([0, 1])
    assert observer1.data_sets_removed.call_args == call([0, 1])
    assert observer2.data_sets_removed.call_args == call([0, 1])


def test_data_manager_loads_partners_for_xye_files(manager, mocker):
    load_mock = mocker.patch.object(manager, 'load')
    manager.data_sets = [create_data_set('prefix_p1_suffix',
                                         path='/path/to/prefix_p1_suffix')]
    manager.load_partners()
    assert load_mock.call_args == call([Path('/path/to/prefix_p2_suffix')])


def test_load_partners_handles_data_set_without_a_path(manager, mocker):
    load_mock = mocker.patch.object(manager, 'load')
    manager.data_sets = [create_data_set('ds1')]
    manager.load_partners()
    assert load_mock.call_args == call([])


def test_merge_partners_for_no_datasets(manager):
    manager.merge_partners(MergePartners.P1_2)
    assert len(manager.data_sets) == 0


def test_merge_partners_with_missing_partner(manager):
    manager.data_sets = [create_data_set('data_set_p1_0')]
    observer = Mock()
    manager.add_observer(observer)
    manager.merge_partners(MergePartners.P1_2)
    assert len(manager.data_sets) == 1
    assert observer.data_sets_added.called is False


def test_merge_partners(manager):
    manager.data_sets = [
        create_data_set('data_set_p1_0', array=P1_ARRAY, path='/ds_p1_0'),
        create_data_set('data_set_p2_0', array=P2_ARRAY, path='/ds_p2_0'),
    ]
    manager.merge_partners(MergePartners.P1_2)
    assert len(manager.data_sets) == 3
    new_data_set = manager.data_sets[-1]
    assert new_data_set.name == 'data_set_p12_s_0'
    assert np.array_equal(new_data_set.angle, P12_SPLICE_MERGED_ARRAY[:, 0])
    assert np.array_equal(new_data_set.intensity, P12_SPLICE_MERGED_ARRAY[:, 1])
    assert np.array_equal(new_data_set.intensity_stdev, P12_SPLICE_MERGED_ARRAY[:, 2])


def test_merge_partners_with_many_data_sets(manager):
    manager.data_sets = [
        create_data_set('data_set_p1_0', array=P1_ARRAY, path='/ds_p1_0'),
        create_data_set('data_set_p2_0', array=P2_ARRAY, path='/ds_p2_0'),
        create_data_set('data_set_p3_0', array=P1_ARRAY, path='/ds_p3_0'),
        create_data_set('data_set_p4_0', array=P1_ARRAY, path='/ds_p4_0'),
    ]
    manager.merge_partners(MergePartners.P3_4)
    assert len(manager.data_sets) == 5
    new_data_set = manager.data_sets[-1]
    assert new_data_set.name == 'data_set_p34_s_0'


def test_merging_triggers_notification(manager):
    manager.data_sets = [
        create_data_set('data_set_p1_0', array=P1_ARRAY, path='/ds_p1_0'),
        create_data_set('data_set_p2_0', array=P2_ARRAY, path='/ds_p2_0'),
    ]
    observer = Mock()
    manager.add_observer(observer)
    manager.merge_partners(MergePartners.P1_2)
    assert observer.data_sets_added.call_args == call([2])
