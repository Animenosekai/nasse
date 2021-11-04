from nasse import exceptions

class MissingArgument(exceptions.NasseException):
    STATUS_CODE = 500
    MESSAGE = "An argument is missing"
    EXCEPTION_NAME = "MISSING_INTERNAL_ARGUMENT"

    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)
