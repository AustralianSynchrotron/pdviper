import pdviper
from tests.fixtures import TEST_FILE1


def test_splicing():
    data_set = pdviper.DataSet.from_xye(TEST_FILE1)
    partner_data_set = data_set.load_partner()
    ds_spliced = pdviper.splice([data_set, partner_data_set])
    assert ds_spliced.name == 'ds1_0000_p12_s_0000'
