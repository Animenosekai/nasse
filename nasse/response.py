"""
This is where the responses and errors are partly processed
"""
import datetime
import dataclasses
import typing

import werkzeug.http
import werkzeug.exceptions

from nasse import config, exceptions, utils


def exception_to_response(value: Exception, config: typing.Optional[config.NasseConfig] = None):
    """
    Internal function to turn an exception to a tuple of values that can be used to make a response
    """
    if isinstance(value, exceptions.NasseException):
        data = value.MESSAGE
        error = value.EXCEPTION_NAME
        code = int(value.STATUS_CODE)
    elif isinstance(value, werkzeug.exceptions.HTTPException):
        code = value.code or 500
        if code >= 500:  # we don't know what kind of exception it might leak
            data = "An error occured on the server while processing your request"
        # we consider that they are fewer non basic exceptions (non 500) that are dangerous to leak (i.e: 4xx errors are related to the client)
        else:
            data = value.description
        error = " ".join(utils.sanitize.split_on_uppercase(value.__class__.__name__)).upper().strip().replace(" ", "_")
    else:
        # converts class names to error names: NasseException -> NASSE_EXCEPTION
        if isinstance(value, type):
            error = " ".join(utils.sanitize.split_on_uppercase(value.__name__)).upper().strip().replace(" ", "_")
        else:
            error = " ".join(utils.sanitize.split_on_uppercase(value.__class__.__name__)).upper().strip().replace(" ", "_")
        if config and config.debug:
            data = "An error occured on the server while processing your request ({error})".format(error=value)
        else:
            data = "An error occured on the server while processing your request"
        code = 500
    if not data:
        data = "An error occured on the server while processing your request"
    return data, error, code


def cookie_validation(value):
    """
    Internal function to validate a value that needs to be a `ResponseCookie` instance
    """
    try:
        if isinstance(value, ResponseCookie):
            return value.__copy__()
        if isinstance(value, str):
            return ResponseCookie(key=value)
        if utils.unpack.is_unpackable(value):
            try:
                return ResponseCookie(**value)
            except TypeError:
                raise exceptions.validate.CookieConversionError(
                    "Either 'name' is missing or one argument doesn't have the right type while creating a Nasse.response.ResponseCookie instance")
        raise ValueError  # will be catched
    except Exception as err:
        if isinstance(err, exceptions.NasseException):
            raise err
        raise exceptions.validate.CookieConversionError(
            "Nasse cannot convert value of type <{t}> to Nasse.response.ResponseCookie".format(t=value.__class__.__name__))


@dataclasses.dataclass
class ResponseCookie:
    """Represents a cookie to send back"""
    key: str
    value: str = ""
    max_age: typing.Optional[typing.Union[float, datetime.timedelta]] = None
    expires: typing.Optional[typing.Union[float, datetime.datetime]] = None
    path: typing.Union[str, tuple, bytes] = "/"
    domain: typing.Optional[typing.Union[str, bytes]] = None
    secure: bool = False
    httponly: bool = False
    samesite = None
    charset: str = "utf-8"
    max_size: int = 4093

    def __post_init__(self):
        self.expires = self.expires or datetime.datetime.now() + datetime.timedelta(days=30)

    def dumps(self) -> str:
        """
        Creates a header value (string) for the given cookie

        Returns
        -------
        str
            The cookie value
        """
        return werkzeug.http.dump_cookie(**dataclasses.asdict(self))


class Response:
    """Represents a response"""

    # Holds the different type arguments
    # Warning: Should only be modified in a copy of the class
    __returning__ = None

    def __class_getitem__(cls, args):
        """
        Called when giving type arguments to the class.

        Parameters
        ----------
        cls: Response
            The actual class which is being instantiated
        args
            The arguments passed with the type

        Example
        -------
        >>> from nasse import Response, Return
        >>> @app.route
        >>> def hello(username: str = "someone") -> Response[Return(example={"hello": "someone"})]:
        ...     return {"hello": username}

        Returns
        -------
        Response
            The instantiated class
        """
        class NewResponse(cls):
            """A subclass containing the type arguments"""
            __returning__ = args if not isinstance(args, tuple) else list(args)

        NewResponse.__name__ = cls.__name__

        return NewResponse

    def __init__(self,
                 data: typing.Any = None,
                 message: typing.Optional[str] = None,
                 error: typing.Optional[str] = None,
                 code: typing.Optional[int] = None,
                 headers: typing.Optional[typing.Dict[str, str]] = None,
                 cookies: typing.Optional[typing.List[ResponseCookie]] = None,
                 content_type: typing.Optional[str] = None) -> None:
        """
        A Response object given to Nasse to format the response

        Parameters
        ----------
        data: typing.Any, default = None
            The data returned to the client
            if 'data' is None, nothing extra is returned to the client
        message: str, default = None
            The message returned to the client
        error: str, default = None
            If an error occured, the error name (i.e the client is not correctly authenticated, you might want to set this as "AUTH_ERROR"
        code: int, default = 200
            The status code to return
        headers: dict[str, str], default = None
            The extra headers to send back (i.e headers=[{"X-NASSE-AUTH": "nasse+1very12897,cool1212798,128129token"}])
        cookies: dict[str, str], default = None
            The cookies to send back
        """
        cookies = cookies or []

        self.data = data

        if isinstance(error, Exception):
            temp_data, error, temp_code = exception_to_response(error)
        else:
            temp_data, temp_code = None, 200

        data = data or temp_data

        code = code or temp_code

        self.error = str(error) if error is not None else None
        self.code = int(code)
        self.message = str(message) if message is not None else None

        self.headers = {}
        if utils.unpack.is_unpackable(headers):
            # headers: {"HEADER-KEY": "Header Value"}
            for header_key, header_value in dict(headers).items():
                self.headers[str(header_key)] = str(header_value)
        elif isinstance(headers, typing.Iterable):
            if isinstance(headers[0], typing.Iterable) and len(headers[0]) == 2:
                # headers: [("HEADER-KEY", "Header Value")]
                for element in headers:
                    self.headers[str(element[0])] = str(element[1])
            elif len(headers) == 2:
                # headers: ("HEADER-KEY", "Header Value")
                self.headers[str(headers[0])] = str(headers[1])

        if content_type:
            self.headers["Content-Type"] = str(content_type)

        self.cookies = []
        if cookies is not None:
            if utils.unpack.is_unpackable(cookies):
                for key, val in dict(cookies).items():
                    item = {"key": str(key)}
                    item.update(val)
                    self.cookies.append(cookie_validation(item))
            elif isinstance(cookies, typing.Iterable):
                for item in cookies:
                    self.cookies.append(cookie_validation(item))
            else:
                self.cookies.append(cookie_validation(cookies))
                raise exceptions.validate.CookieConversionError(
                    "Nasse cannot convert value of type <{t}> to Nasse.response.ResponseCookie".format(t=cookies.__class__.__name__))

    def __copy__(self):
        return Response(
            data=self.data,
            message=self.message,
            error=self.error,
            code=self.code,
            headers=self.headers,
            cookies=self.cookies
        )


def hello() -> Response[{"hello": "world"}]:
    """Hello"""
    return Response()
