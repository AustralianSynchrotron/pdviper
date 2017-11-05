class XyDataPresenter:

    def __init__(self, *, x_scales=None, y_scales=None):
        self.data_sets = []
        self._x_scales = x_scales or [AxisScaler(name='X', transformation=lambda x: x)]
        self._y_scales = y_scales or [AxisScaler(name='Y', transformation=lambda x: x)]
        self._active_x_scale = self._x_scales[0]
        self._active_y_scale = self._y_scales[0]

    @property
    def x_scale_options(self):
        return [s.name for s in self._x_scales]

    @property
    def y_scale_options(self):
        return [s.name for s in self._y_scales]

    def set_x_scale(self, name):
        self._active_x_scale = next(s for s in self._x_scales if s.name == name)

    def set_y_scale(self, name):
        self._active_y_scale = next(s for s in self._y_scales if s.name == name)

    @property
    def x_axis_label(self):
        return self._active_x_scale.axis_label

    @property
    def y_axis_label(self):
        return self._active_y_scale.axis_label

    @property
    def series(self):
        return XySeriesCollection(self.data_sets,
                                  x_scaler=self._active_x_scale,
                                  y_scaler=self._active_y_scale)


class XySeriesCollection:
    def __init__(self, data_sets, *, x_scaler, y_scaler):
        self._data_sets = data_sets
        self._x_scaler = x_scaler
        self._y_scaler = y_scaler

    def __getitem__(self, index):
        return XySeries(self._data_sets[index],
                        x_scaler=self._x_scaler,
                        y_scaler=self._y_scaler)

    def __len__(self):
        return len(self._data_sets)


class XySeries:
    def __init__(self, data_set, *, x_scaler, y_scaler):
        self.x = x_scaler.transform(data_set.angle)
        self.y = y_scaler.transform(data_set.intensity)
        self.name = data_set.name


def _first_or_none(collection):
    return list(collection)[0] if collection else None


class AxisScaler:
    def __init__(self, name, *, axis_label=None, transformation=None):
        self.name = name
        self.axis_label = axis_label or name
        self.transformation = transformation

    def transform(self, array):
        return self.transformation(array) if self.transformation else array
