from pathlib import Path
from unittest.mock import Mock

import pytest

from pdviper.data_manager import DataManager


TEST_FILE_PATH = str(Path(__file__).parent / '../fixtures/file1.xye')


@pytest.fixture
def manager():
    yield DataManager()


def test_data_manager_adds_callbacks(manager):
    callback1 = Mock()
    callback2 = Mock()
    manager.add_callback(callback1)
    manager.add_callback(callback2)
    manager.load([TEST_FILE_PATH])
    assert callback1.called is True
    assert callback2.called is True


def test_data_manager_removes_callbacks(manager):
    callback1 = Mock()
    callback2 = Mock()
    manager.add_callback(callback1)
    manager.add_callback(callback2)
    manager.remove_callback(callback1)
    manager.load([TEST_FILE_PATH])
    assert callback1.called is False
    assert callback2.called is True
