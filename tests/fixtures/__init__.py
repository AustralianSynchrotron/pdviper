from pathlib import Path

import numpy as np


_dir = Path(__file__).parent

TEST_FILE1 = str(_dir / 'ds1_0000_p1_0000.xye')
TEST_FILE2 = str(_dir / 'ds1_0000_p2_0000.xye')

P1_ARRAY = np.load(_dir / 'p1.npy')
P2_ARRAY = np.load(_dir / 'p2.npy')
P12_SPLICE_MERGED_ARRAY = np.load(_dir / 'p12_splice_merged.npy')
