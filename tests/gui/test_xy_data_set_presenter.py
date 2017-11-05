import numpy as np

import pytest  # noqa

from pdviper.gui.xy_plot.presenter import XyDataPresenter, AxisScaler
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


@pytest.mark.wip
def test_XyDataPresenter_lists_scales():
    presenter = XyDataPresenter(
        x_scales=[
            AxisScaler(name='degrees'),
            AxisScaler(name='radians', transformation=lambda x: x * np.pi / 180),
        ],
        y_scales=[
            AxisScaler(name='linear'),
            AxisScaler(name='log', transformation=lambda x: np.log(x)),
        ],
    )
    assert presenter.x_scale_options == ['degrees', 'radians']
    assert presenter.y_scale_options == ['linear', 'log']


def test_XyDataPresenter_allows_selecting_scale():
    presenter = XyDataPresenter(
        x_scales=[
            AxisScaler(name='degrees', axis_label='Angle (deg)'),
            AxisScaler(name='radians', axis_label='Angle (rad)'),
        ],
        y_scales=[
            AxisScaler(name='linear', axis_label='Linear'),
            AxisScaler(name='log', axis_label='Log'),
        ],
    )
    presenter.set_x_scale('radians')
    presenter.set_y_scale('log')
    assert presenter.x_axis_label == 'Angle (rad)'
    assert presenter.y_axis_label == 'Log'


def test_XyDataPresenter_applies_first_transform_by_default():
    presenter = XyDataPresenter(
        x_scales=[
            AxisScaler(name='doubled', transformation=lambda x: x * 2),
            AxisScaler(name='normal', transformation=None),
        ],
        y_scales=[
            AxisScaler(name='halved', transformation=lambda x: x / 2),
        ],
    )
    presenter.data_sets = [DATA_SET]
    assert np.array_equal(presenter.series[0].x, [0, 2, 4])
    assert np.array_equal(presenter.series[0].y, [4.5, 4, 3.5])


def test_XyDataPresenter_handles_no_transforms():
    presenter = XyDataPresenter()
    presenter.data_sets = [DATA_SET]
    assert np.array_equal(presenter.series[0].x, np.array([0, 1, 2]))
    assert np.array_equal(presenter.series[0].y, np.array([9, 8, 7]))
