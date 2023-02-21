"""
This folder contains the different HTTP WSGI server backends
"""
import abc
from nasse import config


class ABC(metaclass=abc.ABCMeta):
    """Helper class that provides a standard way to create an ABC using
    inheritance.

    Added in the ABC module in Python 3.4
    """
    __slots__ = ()


class ServerBackend(ABC):
    """
    A server backend
    """

    def __init__(self, app: "Nasse", config: config.NasseConfig) -> None:
        self.app = app
        self.config = config or config.NasseConfig()

    @abc.abstractmethod
    def run(self, *args, **kwargs):
        """
        Should contain the server running logic
        """
        return None

    @abc.abstractmethod
    def stop(self):
        """
        Should contain the server termination logic
        """
