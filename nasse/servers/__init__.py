"""
This folder contains the different HTTP WSGI server backends
"""
import abc
from nasse import config


class ServerBackend(abc.ABC):
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
