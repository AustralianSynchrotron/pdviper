from pathlib import Path
from itertools import product
from enum import Enum
import re

import pandas as pd
import numpy as np


class DataManager:
    def __init__(self):
        self.data_sets = []
        self._observers = set()

    def load(self, paths):
        paths = self._discard_paths_that_dont_exist(paths)
        paths = self._discard_paths_that_have_already_been_loaded(paths)
        if not paths:
            return
        start_index = len(self.data_sets)
        self.data_sets.extend(DataSet.from_xye(p) for p in paths)
        stop_index = len(self.data_sets)
        self._notify_observers('data_sets_added', list(range(start_index, stop_index)))

    def remove(self, indexes):
        sorted_indexes = list(sorted(indexes))
        for index in reversed(sorted_indexes):
            del self.data_sets[index]
        self._notify_observers('data_sets_removed', sorted_indexes)

    def load_partners(self):
        paths = []
        for ds in self.data_sets:
            try:
                paths.append(ds.determine_partner_path())
            except CannotResolvePartner:
                continue
        self.load(paths)

    def merge_partners(self, positions):
        partner_data_sets = []
        seen = set()
        for ds1, ds2 in product(self.data_sets, self.data_sets):
            if ds1.position not in positions.value or ds1 in seen:
                continue
            if ds1.determine_partner_name() == ds2.name:
                partner_data_sets.append((ds1, ds2))
                seen.update({ds1, ds2})
        if not partner_data_sets:
            return
        len_before = len(self.data_sets)
        for ds1, ds2 in partner_data_sets:
            new_ds = splice([ds1, ds2])
            self.data_sets.append(new_ds)
        len_after = len(self.data_sets)
        self._notify_observers('data_sets_added', list(range(len_before, len_after)))

    def add_observer(self, observer):
        self._observers.add(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def _notify_observers(self, method_name, indices):
        for observer in self._observers:
            method = getattr(observer, method_name, None)
            if method:
                method(indices)

    def _discard_paths_that_dont_exist(self, paths):
        paths = (Path(p) for p in paths)
        return [p for p in paths if p.exists()]

    def _discard_paths_that_have_already_been_loaded(self, paths):
        loaded_paths = {ds.path for ds in self.data_sets if ds.path is not None}
        return [p for p in paths if p not in loaded_paths]


class DataSet:
    """A single data set of diffraction data.

    Attributes:
        name (str): Name of data set
        angle (array[float]): Angle values in degrees
        intensity (array[float]): Intensity values
        intensity_stdev (array[float]): Standard deviation of intensity values
        path (Path): Path to data set file

    """
    def __init__(self, name, angle, intensity, intensity_stdev, path=None):
        self.name = name
        self.angle = np.array(angle, 'float64')
        self.intensity = np.array(intensity, 'float64')
        self.intensity_stdev = np.array(intensity_stdev, 'float64')
        self.path = Path(path) if path is not None else None
        self._array = np.hstack([self.angle[:, None],
                                 self.intensity[:, None],
                                 self.intensity_stdev[:, None]])

    @property
    def data(self):
        return self._array

    @classmethod
    def from_xye(cls, path):
        path = Path(path)
        name = path.stem
        columns = ['angle', 'intensity', 'intensity_stdev']
        df = pd.read_csv(path, delimiter=' ', names=columns, index_col=False)
        angle = df.angle.values
        intensity = df.intensity.values
        intensity_stdev = df.intensity_stdev.values
        return cls(name, angle, intensity, intensity_stdev, path)

    @property
    def position(self):
        if hasattr(self, '_position'):
            return self._position
        for pos in Position:
            if f'_p{pos.value}_' in self.name.lower():
                break
        else:
            pos = None
        self._position = pos
        return self._position

    def determine_partner_path(self):
        if self.path is None:
            raise CannotResolvePartner('path not set for {self.name}')
        return self.path.with_name(self.determine_partner_name() + self.path.suffix)

    def determine_partner_name(self):
        if self.position is None:
            raise CannotResolvePartner(f'cannot determine position for {self.name}')
        partner_position = MergePartners.partner_to(self.position)
        partner_name = self.name
        for prefix in ['p', 'P']:
            partner_name = partner_name.replace(f'_{prefix}{self.position.value}_',
                                                f'_{prefix}{partner_position.value}_')
        return partner_name

    def load_partner(self):
        return type(self).from_xye(self.determine_partner_path())


class CannotResolvePartner(Exception):
    pass


class Position(Enum):
    P1 = '1'
    P2 = '2'
    P3 = '3'
    P4 = '4'
    P12 = '12'
    P34 = '34'
    P1234 = '1234'


class MergePartners(Enum):
    P1_2 = (Position.P1, Position.P2)
    P3_4 = (Position.P3, Position.P4)
    P12_34 = (Position.P12, Position.P34)

    @classmethod
    def from_positions(cls, *positions):
        return cls(positions)

    @classmethod
    def partner_to(cls, position):
        for partners in cls:
            if position in partners.value:
                break
        else:
            raise ValueError(f'no known partner to {position.name}')
        p1, p2 = partners.value
        return p2 if position == p1 else p1

    @property
    def resulting_position(self):
        return {
            self.P1_2: Position.P12,
            self.P3_4: Position.P34,
            self.P12_34: Position.P1234,
        }[self]


def splice(data_sets):
    no_pos_ds = next((d for d in data_sets if d.position is None), None)
    if no_pos_ds:
        raise ValueError(f'cannot determine position for {no_pos_ds.name}')
    ds1, ds2 = sorted(data_sets, key=lambda ds: ds.position.value)
    try:
        partners = MergePartners.from_positions(ds1.position, ds2.position)
    except ValueError as exc:
        raise ValueError('cannot splice data sets from positions '
                         f'{ds1.position.value} and {ds2.position.value}') from exc
    arr1, arr2 = ds1._array, ds2._array
    arr1 = _remove_gap_neighbours(arr1)
    arr2 = _remove_gap_neighbours(arr2)
    combined_arr = _combine_by_splice(arr1, arr2)
    return DataSet(
        name=_name_for_combined_data(ds1.name, partners),
        angle=combined_arr[:, 0],
        intensity=combined_arr[:, 1],
        intensity_stdev=combined_arr[:, 2],
    )


def _name_for_combined_data(source_name, partners):
    new_position = partners.resulting_position

    def _build_repl_string(match):
        pos_char, = match.groups()
        return f'_{pos_char}{new_position.value}_s_'

    search_position = partners.value[0].value
    search_regex = re.compile(f'_([pP]){search_position}_')
    return search_regex.sub(_build_repl_string, source_name)


def _remove_gap_neighbours(data, gap_threshold=0.1, shave_number=5):
    """Remove readings neighbouring gaps

    Gaps in the detector array lead to gaps in the data and corruption of the sample
    values adjacent to the gaps. Therefore this routine is called prior to merging the
    data for the two detector positions to remove 5 (currently) samples from each side of
    the identified gaps.

    Args:
        data (ndarray): a NxM numpy array of xy data where the first column is angle.
        gap_threshold (float): distance between neighbouring angle values to be
            considered a gap
        shave_number (int): number of values to remove either side of a gap

    """
    # Gaps are 0.5 deg each whereas data points are typically spaced by about 0.00375 deg
    gap_indices = np.where(np.diff(data[:, 0]) > gap_threshold)[0]
    # Now gap_indices contains indices of samples on the LHS of the gap
    # Expand indices into ranges +/- shave_number
    shave_range = np.arange(1 - shave_number, 1 + shave_number)
    deletion_indices = gap_indices[np.newaxis].T + shave_range
    return np.delete(data, deletion_indices, axis=0)


def _combine_by_splice(d1, d2, gap_threshold=0.1):
    """
    d1 and d2 are Nx3 arrays of xye data.
    Replace the 'gaps' in d1 by valid data in the corresponding parts of d2.
    Assumes that the 'gaps' in d1 have been cleaned by a call to clean_gaps().
    """
    # Identify the gaps in d1
    gap_indices = np.where(np.diff(d1[:, 0]) > gap_threshold)[0]
    # get the x or 2theta value ranges for the samples at the edges of the gaps in d1
    x_edges = np.c_[d1[:, 0][gap_indices], d1[:, 0][gap_indices + 1]]
    # for each identified gap in d1, insert that segment from d2
    d1 = d1[:]
    for lower, upper in x_edges:
        new_segment = d2[(d2[:, 0] > lower) & (d2[:, 0] < upper)]
        d1 = _combine_by_merge(d1, new_segment)
    return d1


def _combine_by_merge(d1, d2):
    """
    d1 and d2 are Nx3 arrays of xye data.
    Merge the data sets by combining all data points in x-sorted order.
    Assumes that the 'gaps' in d1 have been cleaned by a call to clean_gaps().
    If any points have exactly duplicated x values the d2 point is not merged.
    """
    combined = np.vstack([d1, d2])
    indices = combined[:, 0].argsort()
    new_data = combined[indices]
    x = new_data[:, 0]
    # Remove duplicate x values that interfere with interpolation
    x_diff = np.diff(x)
    # Don't forget the first element, which doesn't have a diff result yet
    x_diff = np.r_[1, x_diff]
    # Only take the unique values from the array
    x_uniq = x_diff > 0
    return new_data[x_uniq]
