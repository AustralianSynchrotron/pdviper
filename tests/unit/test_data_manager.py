from unittest.mock import Mock, call

import pytest

from pdviper.data_manager import DataManager, DataSet

from tests.fixtures import TEST_FILE1


def create_data_set(name):
    return DataSet(name=name, angle=[], intensity=[], intensity_stdev=[])


@pytest.fixture
def manager():
    yield DataManager()


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
