"""
File containing the different exceptions which can be raised in Nasse
"""

from nasse import logging


class NasseException(Exception):
    STATUS_CODE = 500
    MESSAGE = "An unexpected error occured on the server"
    EXCEPTION_NAME = "SERVER_ERROR"

    def __init__(self, message: str = None, *args: object) -> None:
        if message is not None:
            self.MESSAGE = str(message)
        super().__init__(self.MESSAGE, *args)
        logging.log(self.MESSAGE, level=logging.LogLevels.ERROR)


class NasseExceptionTBD(NasseException):
    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)
