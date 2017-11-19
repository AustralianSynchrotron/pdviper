import numpy as np

import pytest  # noqa

from pdviper.gui.heatmap.presenter import HeatmapDataPresenter
from pdviper.data_manager import DataSet


DATA_SETS = [
    DataSet(name='ds1', angle=[0, 1, 2], intensity=[9, 8, 7], intensity_stdev=[.5, .5, .5]),
    DataSet(name='ds2', angle=[0, 1, 2], intensity=[6, 5, 4], intensity_stdev=[.5, .5, .5]),
]


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
    presenter.data_sets = [
        DataSet(name='ds1', angle=[0, 1, 2], intensity=[9, 8, 7],
                intensity_stdev=[.5, .5, .5]),
        DataSet(name='ds2', angle=[0, 1, 2, 3], intensity=[6, 5, 4, 3],
                intensity_stdev=[.5, .5, .5, .5]),
    ]
    assert np.array_equal(presenter.data, np.array([[9, 8, 7], [6, 5, 4]]))


def test_HeatmapDataPresenter_interpolates_missing_steps(presenter):
    presenter.data_sets = [
        DataSet(name='ds1', angle=[0, 1, 2], intensity=[9, 8, 7],
                intensity_stdev=[.5, .5, .5]),
        DataSet(name='ds2', angle=[0, 2], intensity=[6, 4],
                intensity_stdev=[.5, .5]),
    ]
    assert np.array_equal(presenter.data, np.array([[9, 8, 7], [6, 5, 4]]))


# def test_HeatmapDataPresenter_lists_scales():
#     presenter = HeatmapDataPresenter(
#         x_scales=[
#             AxisScaler(name='degrees'),
#             AxisScaler(name='radians', transformation=lambda x: x * np.pi / 180),
#         ],
#         y_scales=[
#             AxisScaler(name='linear'),
#             AxisScaler(name='log', transformation=lambda x: np.log(x)),
#         ],
#     )
#     assert presenter.x_scale_options == ['degrees', 'radians']
#     assert presenter.y_scale_options == ['linear', 'log']


# def test_HeatmapDataPresenter_allows_selecting_scale():
#     presenter = HeatmapDataPresenter(
#         x_scales=[
#             AxisScaler(name='degrees', axis_label='Angle (deg)'),
#             AxisScaler(name='radians', axis_label='Angle (rad)'),
#         ],
#         y_scales=[
#             AxisScaler(name='linear', axis_label='Linear'),
#             AxisScaler(name='log', axis_label='Log'),
#         ],
#     )
#     presenter.set_x_scale('radians')
#     presenter.set_y_scale('log')
#     assert presenter.x_axis_label == 'Angle (rad)'
#     assert presenter.y_axis_label == 'Log'


# def test_HeatmapDataPresenter_applies_first_transform_by_default():
#     presenter = HeatmapDataPresenter(
#         x_scales=[
#             AxisScaler(name='doubled', transformation=lambda x: x * 2),
#             AxisScaler(name='normal', transformation=None),
#         ],
#         y_scales=[
#             AxisScaler(name='halved', transformation=lambda x: x / 2),
#         ],
#     )
#     presenter.data_sets = [DATA_SET]
#     assert np.array_equal(presenter.series[0].x, [0, 2, 4])
#     assert np.array_equal(presenter.series[0].y, [4.5, 4, 3.5])


# def test_HeatmapDataPresenter_handles_no_transforms():
#     presenter = HeatmapDataPresenter()
#     presenter.data_sets = [DATA_SET]
#     assert np.array_equal(presenter.series[0].x, np.array([0, 1, 2]))
#     assert np.array_equal(presenter.series[0].y, np.array([9, 8, 7]))
