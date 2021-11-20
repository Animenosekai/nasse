from nasse.exceptions.base import NasseException


class ClientError(NasseException):
    STATUS_CODE = 400
    MESSAGE = "Something is missing from the request"
    EXCEPTION_NAME = "CLIENT_ERROR"

    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)


class MissingValue(ClientError):
    MESSAGE = "A value is missing from your request"
    EXCEPTION_NAME = "MISSING_VALUE"

    def __init__(self, name: str = "", missing_type: str = "value", *args: object) -> None:
        message = "'{name}' is a required request {type}".format(
            name=name, type=str(missing_type))
        super().__init__(message=message, *args)


class MissingParam(MissingValue):
    MESSAGE = "A parameter is missing from your request"
    EXCEPTION_NAME = "MISSING_PARAM"

    def __init__(self, name: str = "", missing_type: str = "parameter", *args: object) -> None:
        super().__init__(name=name, missing_type=missing_type, *args)


class MissingDynamic(MissingValue):
    MESSAGE = "A dynamic routing value is missing from your request"
    EXCEPTION_NAME = "MISSING_DYNAMIC"

    def __init__(self, name: str = "", missing_type: str = "parameter", *args: object) -> None:
        super().__init__(name=name, missing_type=missing_type, *args)


class MissingHeader(MissingValue):
    MESSAGE = "A header is missing from your request"
    EXCEPTION_NAME = "MISSING_HEADER"

    def __init__(self, name: str = "", missing_type: str = "header", *args: object) -> None:
        super().__init__(name=name, missing_type=missing_type, *args)


class MissingCookie(MissingValue):
    MESSAGE = "A cookie is missing from your request"
    EXCEPTION_NAME = "MISSING_COOKIE"

    def __init__(self, name: str = "", missing_type: str = "cookie", *args: object) -> None:
        super().__init__(name=name, missing_type=missing_type, *args)


class MissingContext(NasseException):
    MESSAGE = "You are not actively in a Nasse context"
    EXCEPTION_NAME = "MISSING_CONTEXT"
    STATUS_CODE = 500

    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)


class MissingEndpoint(MissingContext):

    def __init__(self, message: str = None, *args: object) -> None:
        super().__init__(message=message, *args)
