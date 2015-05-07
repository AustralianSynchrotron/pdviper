

class BasePlot(object):
    def prepare_data(self, stack):
        return self._prepare_data(stack)

    def plot(self, *data, **kwargs):
        self.component = self._plot(*data, **kwargs)
        return self.component

    def reset_view(self):
        self._reset_view()

