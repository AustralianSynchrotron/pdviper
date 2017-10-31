from inspect import signature
from abc import ABC, abstractmethod
from enum import IntEnum


class XyLegendState(IntEnum):
    OFF = 0
    ON = 1


class XyPlotWidget(ABC):
    @abstractmethod
    def plot(self):
        ...


def verify_class_implements_abc(Concrete, Abc):
    for method_name in Abc.__abstractmethods__:
        try:
            concrete_method_sig = signature(getattr(Concrete, method_name))
        except AttributeError as exc:
            raise TypeError(f'{Concrete.__name__} must implement '
                            f'abstract method {method_name}') from exc
        else:
            if concrete_method_sig != signature(getattr(Abc, method_name)):
                raise TypeError('invalid signature for '
                                f'{Concrete.__name__}.{method_name}')
