from pathlib import Path

from pdviper.data_manager import DataSet


TEST_FILE_PATH = str(Path(__file__).parent / '../fixtures/file1.xye')


def test_dataset_sets_sample_name():
    dataset = DataSet.from_xye(TEST_FILE_PATH)
    assert dataset.name == 'file1'
