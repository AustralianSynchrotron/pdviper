

class BasePlot(object):
    def prepare_data(self, datasets):
        return self._prepare_data(datasets)

    def plot(self, *data, **kwargs):
        self.component = self._plot(*data, **kwargs)
        return self.component

