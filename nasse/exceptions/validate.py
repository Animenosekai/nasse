"""
A list of internal exceptions for Nasse validations
"""
from nasse.exceptions.base import NasseException


class ValidationError(NasseException):
    """When there is an input validation error"""
    MESSAGE = "Nasse couldn't validate an input"
    EXCEPTION_NAME = "VALIDATION_ERROR"


class ConversionError(ValidationError):
    """An internal error occuring when Nasse can't convert an input to a Nasse object"""
    EXCEPTION_NAME = "INTERNAL_CONVERSION_ERROR"
    MESSAGE = "Nasse couldn't convert a given input to a Nasse object instance"


class MethodsConversionError(ConversionError):
    """An internal error occuring when Nasse can't convert an input to methods"""


class ReturnConversionError(ConversionError):
    """An internal error occuring when Nasse can't convert an input to a Nasse `Return` object"""


class UserSentConversionError(ConversionError):
    """An internal error occuring when Nasse can't convert an input to a Nasse `UserSent` object"""


class ErrorConversionError(ConversionError):
    """An internal error occuring when Nasse can't convert an input to a Nasse `Error` object"""


class LoginConversionError(ConversionError):
    """An internal error occuring when Nasse can't convert an input to a Nasse `Login` object"""


class CookieConversionError(ConversionError):
    """An internal error occuring when Nasse can't convert an input to a Nasse `Cookie` object"""
