import numpy as np

import pytest  # noqa

from pdviper.gui.heatmap.presenter import HeatmapDataPresenter
from pdviper.data_manager import DataSet, DataSetCollection


DATA_SETS = DataSetCollection([
    DataSet(name='ds1', angle=[0, 1, 2], intensity=[9, 8, 7], intensity_stdev=[.5, .5, .5]),
    DataSet(name='ds2', angle=[0, 1, 2], intensity=[6, 5, 4], intensity_stdev=[.5, .5, .5]),
])


@pytest.fixture
def presenter():
    yield HeatmapDataPresenter(x_step_size=1.0)


def test_HeatmapDataPresenter_has_empty_data_by_default(presenter):
    assert presenter.data.shape == (0, 0)


def test_HeatmapDataPresenter_holds_data_sets(presenter):
    presenter.data_sets = DATA_SETS
    assert presenter.data.shape == (2, 3)
    assert np.array_equal(presenter.data, np.array([[9, 8, 7], [6, 5, 4]]))


def test_HeatmapDataPresenter_handles_data_sets_of_different_sizes(presenter):
    presenter.data_sets = DataSetCollection([
        DataSet(name='ds1', angle=[0, 1, 2], intensity=[9, 8, 7],
                intensity_stdev=[.5, .5, .5]),
        DataSet(name='ds2', angle=[0, 1, 2, 3], intensity=[6, 5, 4, 3],
                intensity_stdev=[.5, .5, .5, .5]),
    ])
    assert np.array_equal(presenter.data, np.array([[9, 8, 7], [6, 5, 4]]))


def test_HeatmapDataPresenter_interpolates_missing_steps(presenter):
    presenter.data_sets = DataSetCollection([
        DataSet(name='ds1', angle=[0, 1, 2], intensity=[9, 8, 7],
                intensity_stdev=[.5, .5, .5]),
        DataSet(name='ds2', angle=[0, 2], intensity=[6, 4],
                intensity_stdev=[.5, .5]),
    ])
    assert np.array_equal(presenter.data, np.array([[9, 8, 7], [6, 5, 4]]))


def test_x_range_gives_overlapping_range(presenter):
    presenter.data_sets = DataSetCollection([
        DataSet(name='ds1', angle=[0, 2], intensity=[0, 0], intensity_stdev=[0, 0]),
        DataSet(name='ds2', angle=[1, 3], intensity=[0, 0], intensity_stdev=[.5, .5]),
    ])
    assert presenter.x_range == (1, 2)
