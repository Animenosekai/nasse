"""
File containing the different exceptions which can be raised in Nasse
"""

import typing
from nasse.exceptions.base import NasseException
from nasse.exceptions import arguments, authentication, request, validate


class NasseExceptionTBD(NasseException):
    """
    If an exception is expected to be defined later on
    """
