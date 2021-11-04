from base64 import b64encode
from sys import getsizeof
from typing import Any, Iterable

from flask import Response as FlaskResponse
from flask import request as flask_request
from flask import g

from nasse import exceptions, models
from nasse.config import Mode
from nasse.utils.ip import get_ip
from nasse.utils.logging import LogLevels, log, Record, Colors
from nasse.request import Request
from nasse.response import Response, exception_to_response
from nasse.timer import Timer
from nasse.utils import json, xml
from nasse.utils.annotations import is_unpackable
from nasse.utils.boolean import to_bool
from nasse.utils.sanitize import remove_spaces

RECEIVERS_COUNT = 0


def retrieve_token(context: Request = None) -> str:
    """
    Internal function to retrieve the login token from a request

    Parameters
    ----------
        context: nasse.request.Request
            The current request, if not properly set, the current context is used.
    """
    if not isinstance(context, Request):
        context = g.request or flask_request
    token = context.headers.get("Authorization", None)
    if token is None:
        # should be app.id + "_token"
        token = context.values.get(
            "{id}_token".format(id=context.nasse.id), None)
        if token is None:
            # should be "__" + app.id + "_token"
            token = context.cookies.get(
                "__{id}_token".format(id=context.nasse.id), None)
            if token is None:
                raise exceptions.authentication.MissingToken(
                    "An authentication token is missing from the request")
    return str(token)


class Receive():
    def __init__(self, app, endpoint: models.Endpoint) -> None:
        """
        This object is called by Flask and receives all of the requests.

        It performs some verification, according to what the user provided for the endpoint
        and sets some important variables, like nasse.request
        """
        global RECEIVERS_COUNT
        self.app = app
        self.endpoint = endpoint
        RECEIVERS_COUNT += 1
        self.__name__ = "__nasse_receiver_{number}".format(
            number=RECEIVERS_COUNT)

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        with Record() as STACK:
            with Timer() as global_timer:
                try:
                    with Timer() as verification_timer:
                        g.request = Request(
                            app=self.app, endpoint=self.endpoint)
                        log("→ Incoming {method} request to {route} from {client}".format(method=g.request.method, route=self.endpoint.path, client=g.request.client_ip),
                            level=LogLevels.INFO)

                    account = None
                    with Timer() as authentication_timer:
                        if not self.endpoint.login.no_login and self.endpoint.login.required:
                            if self.endpoint.login.all_methods or g.request.method in self.endpoint.login.methods:
                                token = retrieve_token()
                                if self.app.account:
                                    account = self.app.account.retrieve_account(
                                        token)
                                    if len(self.endpoint.login.types) > 0:
                                        if self.app.account.retrieve_type(account) not in self.endpoint.login.types:
                                            raise exceptions.authentication.Forbidden(
                                                "You can't access this endpoint with your account")
                                else:
                                    log("Couldn't verify login details because 'account_management' is not set properly on {name}".format(
                                        name=self.app.name), level=LogLevels.WARNING)

                    with Timer() as processing_timer:
                        arguments = {}
                        for attr, current_values in [
                            ("app", self.app),
                            ("nasse", self.app),
                            ("endpoint", self.endpoint),
                            ("nasse_endpoint", self.endpoint),
                            ("request", g.request),
                            ("method", g.request.method),
                            ("values", g.request.values),
                            ("params", g.request.values),
                            ("args", g.request.args),
                            ("form", g.request.form),
                            ("headers", g.request.headers),
                            ("account", account)
                        ]:
                            if attr in self.endpoint.handler.__code__.co_varnames:
                                arguments[attr] = current_values
                        arguments.update(kwds)

                        # calling the request handler
                        response = self.endpoint.handler(*args, **arguments)

                    with Timer() as formatting_timer:
                        if isinstance(response, FlaskResponse):
                            return response

                        data = ""
                        error = None
                        code = 200
                        headers = {}
                        cookies = []

                        if isinstance(response, Response):
                            # return Response(data=..., code=..., etc.)
                            data = response.data
                            code = response.code
                            error = response.error
                            headers = response.headers
                            cookies = response.cookies
                        elif isinstance(response, str):
                            # return "Hello world"
                            data = response
                        elif isinstance(response, Exception):
                            # return NasseException("Something went wrong")
                            data, error, code = exception_to_response(response)
                        elif is_unpackable(response):
                            response = Response(**response)
                            data = response.data
                            code = response.code
                            error = response.error
                            headers = response.headers
                            cookies = response.cookies
                        elif isinstance(response, Iterable):
                            # return "Hello", 200 | return NasseException("..."), 400, {"extra": {"issue": "something is missing"}}
                            for value in response:
                                if isinstance(value, Exception):
                                    data, error, code = exception_to_response(
                                        value)
                                elif isinstance(value, int):
                                    code = int(value)
                                else:
                                    data = value
                        else:
                            # return bytes(data)
                            data = response

                        if code < 100 or code >= 600:
                            log("The returning HTTP status code doesn't seem to be a standard status code: {code}".format(
                                code=code), level=LogLevels.WARNING)

                        if not self.endpoint.json:
                            final = FlaskResponse(response=data, status=code)

                            if error:
                                final.headers["X-NASSE-ERROR"] = str(error)

                            if Mode.DEBUG:
                                final.headers["X-NASSE-TIME-GLOBAL"] = str(
                                    global_timer.stop())
                                final.headers["X-NASSE-TIME-VERIFICATION"] = str(
                                    verification_timer.time)
                                final.headers["X-NASSE-TIME-AUTHENTICATION"] = str(
                                    authentication_timer.time)
                                final.headers["X-NASSE-TIME-PROCESSING"] = str(
                                    processing_timer.time)
                                final.headers["X-NASSE-TIME-FORMATTING"] = str(
                                    formatting_timer.stop())
                        else:
                            result = {
                                "success": error is None,
                                "error": error,
                                "data": {}
                            }
                            if is_unpackable(data):
                                # data: {"username": "someone", "token": "something"}
                                result["data"] = dict(data)
                            elif isinstance(data, bytes):
                                # data: bytes data, raw file content
                                result["data"]["base64"] = b64encode(
                                    data).decode("utf-8")
                            elif hasattr(data, "read") and hasattr(data, "tell") and hasattr(data, "seek"):
                                # a file object
                                position = data.tell()  # storing the current position
                                content = data.read()  # read it (place the cursor at the end)
                                # go back to the original position
                                data.seek(position)
                                if "b" in data.mode:  # if binary mode
                                    result["data"]["base64"] = b64encode(
                                        content).decode("utf-8")  # base64 encode the result
                                else:
                                    result["data"]["content"] = str(content)
                            elif isinstance(data, str):
                                # data: "Hello World"
                                result["data"]["message"] = data
                            elif isinstance(data, Iterable):
                                # data: ["an", "array", "of", "element"] | ("an", "array", ...) | etc.
                                result["data"]["array"] = list(data)
                            else:
                                # data: Any (but json does not support arbitrary content)
                                log(
                                    "Element of type {type} is not supported by JSON and will be converted to `str`".format(type=data.__class__.__name__), level=LogLevels.WARNING)
                                result["data"]["content"] = str(data)
                except Exception as e:
                    try:
                        verification_timer
                    except Exception:
                        verification_timer = None
                    try:
                        authentication_timer
                    except Exception:
                        authentication_timer = None
                    try:
                        processing_timer
                    except Exception:
                        processing_timer = None
                    try:
                        formatting_timer
                    except Exception:
                        formatting_timer = None
                    data, error, code = exception_to_response(e)
                    result = {
                        "success": False,
                        "error": error,
                        "data": {
                            "message": data
                        }
                    }
                    try:
                        g.request
                    except Exception:
                        g.request = flask_request
                    try:
                        cookies
                    except Exception:
                        cookies = []
                    try:
                        headers
                    except Exception:
                        headers = {}

                CALL_STACK, LOG_STACK = STACK.stop()
                if Mode.DEBUG:
                    result["debug"] = {
                        "time": {
                            "global": global_timer.stop(),
                            "verification": verification_timer.time if verification_timer is not None else None,
                            "authentication": authentication_timer.time if authentication_timer is not None else None,
                            "processing": processing_timer.time if processing_timer is not None else None,
                            "formatting": formatting_timer.stop() if formatting_timer is not None else None
                        },
                        "ip": g.request.client_ip if isinstance(g.request, Request) else get_ip(),
                        "headers": dict(g.request.headers),
                        "values": dict(g.request.values),
                        "domain": g.request.host,
                        "logs": LOG_STACK,
                        "call_stack": ["pass the 'call_stack' parameter to get the call stack"]
                    }

                    if "call_stack" in g.request.values:
                        result["debug"]["call_stack"] = [frame.as_dict()
                                                         for frame in CALL_STACK]

                minify = to_bool(g.request.values.get("minify", False))

                content_type = "application/json"
                if remove_spaces(g.request.values.get("format", "json")).lower() in {"xml", "html"}:
                    body = xml.encode(data=result, minify=minify)
                    content_type = "application/xml"
                else:
                    body = (json.minified_encoder if minify else json.encoder).encode(
                        result)

                final = FlaskResponse(body, status=code)
                final.headers["Content-Type"] = content_type

            # final is now defined
            for cookie in cookies:
                # 'cookie' should be a ResponseCookie
                final.headers.add("Set-Cookie", cookie.dumps())

            for key, value in headers.items():
                final.headers[str(key)] = str(value)

            try:
                if isinstance(g.request, Request):
                    path = g.request.nasse_endpoint.path
                    ip = g.request.client_ip
                    method = g.request.method
                else:
                    path = g.request.path
                    ip = get_ip()
                    method = str(g.request.method).upper()
                size = getsizeof(final.data)
                print(size)
                if size < 500000:
                    color = Colors.green
                elif size < 1000000:
                    color = Colors.yellow
                else:
                    color = Colors.magenta
                log("← Sending back {color}{size}{normal} bytes of data to {ip} following {method} {path}".format(
                    color=color,
                    size=size,
                    normal=Colors.normal,
                    ip=ip,
                    method=method,
                    path=path
                ))
            except Exception:
                pass
            return final
