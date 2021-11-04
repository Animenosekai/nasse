from nasse.exceptions.base import NasseException


class ValidationError(NasseException):
    MESSAGE = "Nasse couldn't validate an input"
    EXCEPTION_NAME = "VALIDATION_ERROR"

    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)


class ConversionError(ValidationError):
    EXCEPTION_NAME = "INTERNAL_CONVERSION_ERROR"
    MESSAGE = "Nasse couldn't convert a given input to a Nasse object instance"

    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)


class MethodsConversionError(ConversionError):
    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)


class ReturnConversionError(ConversionError):
    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)


class UserSentConversionError(ConversionError):
    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)


class ErrorConversionError(ConversionError):
    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)


class LoginConversionError(ConversionError):
    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)


class CookieConversionError(ConversionError):
    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)
