"""
File containing the different exceptions which can be raised in Nasse
"""
from nasse.exceptions.base import NasseException
from nasse.exceptions import arguments, authentication, request, validate

class NasseExceptionTBD(NasseException):
    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)
