"""
Internal Nasse error about arguments
"""

import typing
from nasse.exceptions.base import NasseException


class MissingArgument(NasseException):
    """When an argument is missing"""
    STATUS_CODE = 500
    MESSAGE = "An argument is missing"
    EXCEPTION_NAME = "MISSING_INTERNAL_ARGUMENT"
