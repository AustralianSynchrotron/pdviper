from inspect import signature


class ImageFormat:
    def __init__(self, name, extension):
        self.name = name
        self.extension = extension

    @property
    def qt_filter(self):
        return f'{self.name} (*.{self.extension})'

    def __repr__(self):
        return f'<{type(self).__name__}: {self.name}>'


def verify_class_implements_abc(Concrete, Abc):
    for method_name in Abc.__abstractmethods__:

        if isinstance(getattr(Abc, method_name), property):

            try:
                getattr(Concrete, method_name)
            except AttributeError as exc:
                raise TypeError(f'{Concrete.__name__} must provide attribute '
                                f'{method_name}') from exc

        else:

            try:
                concrete_method_sig = signature(getattr(Concrete, method_name))
            except AttributeError as exc:
                raise TypeError(f'{Concrete.__name__} must implement '
                                f'abstract method {method_name}') from exc
            else:
                if concrete_method_sig != signature(getattr(Abc, method_name)):
                    raise TypeError('invalid signature for '
                                    f'{Concrete.__name__}.{method_name}')
