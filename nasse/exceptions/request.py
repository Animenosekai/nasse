from nasse.exceptions.base import NasseException


class ClientError(NasseException):
    """When there is a client side error"""
    STATUS_CODE = 400
    MESSAGE = "Something is missing from the request"
    EXCEPTION_NAME = "CLIENT_ERROR"

class InvalidType(ClientError):
    """When the given parameter is of an invalid type"""
    MESSAGE = "The given value is of an invalid type"
    EXCEPTION_NAME = "INVALID_TYPE"

    def __init__(self, *args: object, name: str = "") -> None:
        message = "The given value `{name}` could not be casted to a valid type".format(name=name)
        super().__init__(message=message, *args)

class MissingValue(ClientError):
    """When a value is missing from the request"""
    MESSAGE = "A value is missing from your request"
    EXCEPTION_NAME = "MISSING_VALUE"

    def __init__(self, *args: object, name: str = "", missing_type: str = "value") -> None:
        message = "`{name}` is a required request {type}".format(name=name,
                                                                 type=str(missing_type))
        super().__init__(message=message, *args)


class MissingParam(MissingValue):
    """When a parameter is missing"""
    MESSAGE = "A parameter is missing from your request"
    EXCEPTION_NAME = "MISSING_PARAM"


class MissingDynamic(MissingValue):
    """When a dynamic routing value is missing"""
    MESSAGE = "A dynamic routing value is missing from your request"
    EXCEPTION_NAME = "MISSING_DYNAMIC"


class MissingHeader(MissingValue):
    """When a header is missing"""
    MESSAGE = "A header is missing from your request"
    EXCEPTION_NAME = "MISSING_HEADER"


class MissingCookie(MissingValue):
    """When a cookie is missing"""
    MESSAGE = "A cookie is missing from your request"
    EXCEPTION_NAME = "MISSING_COOKIE"


class MissingContext(NasseException):
    """Server side error when a value only accessible in a Nasse context is accessed outside of oneƒ"""
    MESSAGE = "You are not actively in a Nasse context"
    EXCEPTION_NAME = "MISSING_CONTEXT"
    STATUS_CODE = 500


class MissingEndpoint(MissingContext):
    """When an endpoint is missing"""
    # ??
