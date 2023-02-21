"""
Defines the base exception
"""

import typing
from nasse.utils.logging import logger


class NasseException(Exception):
    """
    Represents an exception, providing a bit more context for the server to actually give back the best answers possible.

    Here are the different constants which can be set

    - STATUS_CODE: The actual status code to respond with, defaults to 500
    - MESSAGE: A message accompanying the error, optional
    - EXCEPTION_NAME: Explicitely giving the exception name, defaults to "SERVER_ERROR" 
    - LOG: If the error should be logged to the console, defaults to True
    """
    STATUS_CODE = 500
    MESSAGE = "An unexpected error occured on the server"
    EXCEPTION_NAME = "SERVER_ERROR"
    LOG = True

    def __init__(self, *args: object, message: typing.Optional[str] = None) -> None:
        if message is not None:
            self.MESSAGE = str(message)

        super().__init__(self.MESSAGE, *args)

        if self.LOG:
            # should be the context's logger
            logger.error(self.MESSAGE)
