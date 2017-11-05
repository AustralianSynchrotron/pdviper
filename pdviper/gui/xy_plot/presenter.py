class XyDataPresenter:

    def __init__(self, x_transforms=None, y_transforms=None):
        self.data_sets = []
        self.x_transforms = x_transforms or {}
        self.y_transforms = y_transforms or {}
        self.active_x_transform = _first_or_none(self.x_transforms)
        self.active_y_transform = _first_or_none(self.y_transforms)

    @property
    def series(self):
        x_transform = self.x_transforms.get(self.active_x_transform)
        y_transform = self.y_transforms.get(self.active_y_transform)
        return XySeriesCollection(self.data_sets,
                                  x_transform=x_transform,
                                  y_transform=y_transform)


class XySeriesCollection:
    def __init__(self, data_sets, *, x_transform=None, y_transform=None):
        self._data_sets = data_sets
        self._x_transform = x_transform or (lambda o: o)
        self._y_transform = y_transform or (lambda o: o)

    def __getitem__(self, index):
        return XySeries(self._data_sets[index],
                        x_transform=self._x_transform,
                        y_transform=self._y_transform)

    def __len__(self):
        return len(self._data_sets)


class XySeries:
    def __init__(self, data_set, *, x_transform, y_transform):
        self.x = x_transform(data_set.angle)
        self.y = y_transform(data_set.intensity)
        self.name = data_set.name


def _first_or_none(collection):
    return list(collection)[0] if collection else None
