import numpy as np

from pdviper.gui.xy_plot.presenter import XyDataPresenter
from pdviper.data_manager import DataSet


DATA_SET = DataSet(name='test',
                   angle=[0, 1, 2],
                   intensity=[9, 8, 7],
                   intensity_stdev=[.5, .5, .5])


def test_XyDataPresenter_has_empty_data_sets_by_default():
    presenter = XyDataPresenter()
    assert len(presenter.series) == 0


def test_XyDataPresenter_holds_data_sets():
    presenter = XyDataPresenter()
    presenter.data_sets = [DATA_SET]
    assert len(presenter.series) == 1
    series = presenter.series[0]
    assert np.array_equal(series.x, np.array([0, 1, 2]))
    assert np.array_equal(series.y, np.array([9, 8, 7]))
    assert np.array_equal(series.name, 'test')


def test_XyDataPresenter_lists_transforms():
    presenter = XyDataPresenter(
        x_transforms={
            'degrees': None,
            'radians': lambda x: x * np.pi / 180,
        },
        y_transforms={
            'linear': None,
            'log': lambda x: np.log(x),
        },
    )
    assert list(presenter.x_transforms) == ['degrees', 'radians']
    assert list(presenter.y_transforms) == ['linear', 'log']


def test_XyDataPresenter_applies_first_transform_by_default():
    presenter = XyDataPresenter(
        x_transforms={
            'doubled': lambda x: x * 2,
            'normal': None,
        },
        y_transforms={
            'halved': lambda x: x / 2,
        },
    )
    presenter.data_sets = [DATA_SET]
    assert presenter.active_x_transform == 'doubled'
    assert presenter.active_y_transform == 'halved'
    assert np.array_equal(presenter.series[0].x, [0, 2, 4])
    assert np.array_equal(presenter.series[0].y, [4.5, 4, 3.5])


def test_XyDataPresenter_handles_no_transforms():
    presenter = XyDataPresenter()
    presenter.data_sets = [DATA_SET]
    assert presenter.active_x_transform is None
    assert presenter.active_y_transform is None
    assert np.array_equal(presenter.series[0].x, np.array([0, 1, 2]))
    assert np.array_equal(presenter.series[0].y, np.array([9, 8, 7]))
