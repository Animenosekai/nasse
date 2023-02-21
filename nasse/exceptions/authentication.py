"""
Exceptions handling the authentication errors
"""

import typing
from nasse.exceptions.base import NasseException


class AuthenticationError(NasseException):
    """When an error occurs with the user authentication step"""
    MESSAGE = "An error occured while checking your authentication"
    EXCEPTION_NAME = "AUTH_ERROR"
    STATUS_CODE = 403


class MissingToken(AuthenticationError):
    """When the token is missing to authenticate"""
    LOG = False
    MESSAGE = "The authentication token is missing from your request"


class Forbidden(AuthenticationError):
    """When the user is not allowed to access something"""
    MESSAGE = "You are not allowed to access this endpoint"
