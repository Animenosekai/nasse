from nasse.exceptions.base import NasseException


class AuthenticationError(NasseException):
    MESSAGE = "An error occured while checking your authentication"
    EXCEPTION_NAME = "AUTH_ERROR"
    STATUS_CODE = 403

    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)


class MissingToken(AuthenticationError):
    MESSAGE = "The authentication token is missing from your request"

    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)


class Forbidden(AuthenticationError):
    MESSAGE = "You are not allowed to access this endpoint"

    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)
