import abc
from abc import abstractmethod


class ABC(metaclass=abc.ABCMeta):
    """Helper class that provides a standard way to create an ABC using
    inheritance.

    Added in the ABC module in Python 3.4
    """
    __slots__ = ()
