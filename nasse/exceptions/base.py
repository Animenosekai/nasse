
from nasse.utils.logging import log, LogLevels


class NasseException(Exception):
    STATUS_CODE = 500
    MESSAGE = "An unexpected error occured on the server"
    EXCEPTION_NAME = "SERVER_ERROR"

    def __init__(self, message: str = None, *args: object) -> None:
        if message is not None:
            self.MESSAGE = str(message)
        super().__init__(self.MESSAGE, *args)
        log(self.MESSAGE, level=LogLevels.ERROR)
