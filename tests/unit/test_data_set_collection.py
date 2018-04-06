from pdviper.data_manager import DataSetCollection, DataSet


def test_common_angle_span_returns_largest_min_angle_and_smallest_max_angle():
    ds1 = DataSet(name='ds1', angle=[1, 3], intensity=[0, 0], intensity_stdev=[0, 0])
    ds2 = DataSet(name='ds2', angle=[2, 4], intensity=[0, 0], intensity_stdev=[0, 0])
    collection = DataSetCollection([ds1, ds2])
    assert collection.common_angle_span == (2, 3)


def test_common_angle_span_on_empty_collection():
    collection = DataSetCollection()
    assert collection.common_angle_span == (None, None)
