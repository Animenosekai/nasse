
from nasse.utils.logging import Logger, LoggingLevel


class NasseException(Exception):
    STATUS_CODE = 500
    MESSAGE = "An unexpected error occured on the server"
    EXCEPTION_NAME = "SERVER_ERROR"
    LOG = True

    def __init__(self, message: str = None, *args: object) -> None:
        if message is not None:
            self.MESSAGE = str(message)
        super().__init__(self.MESSAGE, *args)
        if self.LOG:
            Logger().log(self.MESSAGE, level=LoggingLevel.ERROR)
