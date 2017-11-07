from unittest.mock import Mock, call

import pytest

from pdviper.data_manager import DataManager

from tests.fixtures import TEST_FILE1


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


def test_data_manager_removes_data_sets(manager):
    assert len(manager.data_sets) == 0
