import base64
import inspect
import sys
import typing

import flask

from nasse import config, exceptions, models, request, timer, utils
from nasse.response import Response, exception_to_response

RECEIVERS_COUNT = 0


def retrieve_token(context: request.Request = None) -> str:
    """
    Internal function to retrieve the login token from a request

    Parameters
    ----------
        context: nasse.request.request.Request
            The current request, if not properly set, the current context is used.
    """
    if not isinstance(context, request.Request):
        context = flask.g.request or flask.request
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

    def __call__(self, *args: typing.Any, **kwds: typing.Any) -> typing.Any:
        with utils.logging.Record() as STACK:
            with timer.Timer() as global_timer:
                try:
                    with timer.Timer() as verification_timer:
                        flask.g.request = request.Request(
                            app=self.app, endpoint=self.endpoint, dynamics=kwds)
                        utils.logging.log("→ Incoming {color}{method}{normal} request to {color}{route}{normal} from {client}".format(method=flask.g.request.method, color=utils.logging.Colors.blue, normal=utils.logging.Colors.normal, route=self.endpoint.path, client=flask.g.request.client_ip),
                                          level=utils.logging.LogLevels.INFO)

                    account = None
                    with timer.Timer() as authentication_timer:
                        method = flask.g.request.method
                        login_rules = self.endpoint.login.get(method, self.endpoint.login.get("*", None))
                        if not login_rules.no_login:
                            try:
                                token = retrieve_token()
                                if self.app.account_management:
                                    if not login_rules.verification_only:
                                        account = self.app.account_management.retrieve_account(
                                            token)
                                        if len(login_rules.types) > 0:
                                            if self.app.account_management.retrieve_type(account) not in login_rules.types:
                                                account = None  # if login is not required, the account might be passed with a wrong type
                                                raise exceptions.authentication.Forbidden("You can't access this endpoint with your account")
                                    else:
                                        verification = self.app.account_management.verify_token(token)
                                        if verification == False:
                                            raise exceptions.authentication.Forbidden("We couldn't verify your token")
                                else:
                                    utils.logging.log("Couldn't verify login details because the 'account_management' is not set properly on {name}".format(
                                        name=self.app.name), level=utils.logging.LogLevels.WARNING)
                            except Exception as e:
                                if login_rules.required:
                                    raise e

                    with timer.Timer() as processing_timer:
                        specs = inspect.getfullargspec(self.endpoint.handler).args
                        arguments = {}

                        for arg in specs:  # for the function arguments
                            for storage in (flask.g.request.values, flask.g.request.headers, flask.g.request.cookies):
                                if arg in storage:
                                    val = storage.getlist(arg)
                                    if len(val) > 1:
                                        arguments[arg] = val
                                    else:
                                        arguments[arg] = val[0]
                                    break

                        if account is not None:
                            arguments.pop("account", None)

                        for attr, current_values in [
                            ("app", self.app),
                            ("nasse", self.app),
                            ("endpoint", self.endpoint),
                            ("nasse_endpoint", self.endpoint),
                            ("request", flask.g.request),
                            ("method", flask.g.request.method),
                            ("values", flask.g.request.values),
                            ("params", flask.g.request.values),
                            ("args", flask.g.request.args),
                            ("form", flask.g.request.form),
                            ("headers", flask.g.request.headers),
                            ("account", account),
                            ("dynamics", flask.g.request.dynamics)
                        ]:
                            if attr in specs and attr not in arguments:
                                arguments[attr] = current_values

                        for key, val in flask.g.request.dynamics.items():  # no need for multi=True as dynamics should only have one value
                            if key in specs:
                                arguments[key] = val

                        # we don't need this because "dynamics" already holds those values
                        # and it saves us from making another loop
                        # arguments.update(kwds)
                        # for arg in arguments:
                        #     if arg not in specs:
                        #         arguments.pop(arg, None)

                        # calling the request handler
                        response = self.endpoint.handler(*args, **arguments)

                    with timer.Timer() as formatting_timer:
                        if isinstance(response, flask.Response):
                            return response

                        data = ""
                        error = None
                        message = None
                        code = 200
                        headers = {}
                        cookies = []

                        if isinstance(response, Response):
                            # return Response(data=..., code=..., etc.)
                            data = response.data
                            code = response.code
                            message = response.message
                            error = response.error
                            headers = response.headers
                            cookies = response.cookies
                        elif isinstance(response, str):
                            # return "Hello world"
                            message = response
                        elif isinstance(response, bytes):
                            # return b"binary data"
                            data = response
                        elif isinstance(response, Exception):
                            # return NasseException("Something went wrong")
                            message, error, code = exception_to_response(response)
                        elif isinstance(response, typing.Iterable):
                            found = False
                            if utils.annotations.is_unpackable(response):
                                try:
                                    response = Response(**response)
                                    data = response.data
                                    code = response.code
                                    error = response.error
                                    headers = response.headers
                                    cookies = response.cookies
                                    message = response.message
                                    found = True
                                except TypeError:
                                    pass
                            if not found:
                                # return "Hello", 200 | return NasseException("..."), 400, {"extra": {"issue": "something is missing"}}
                                for value in response:
                                    if isinstance(value, Exception):
                                        message, error, code = exception_to_response(value)
                                    elif isinstance(value, int):
                                        code = int(value)
                                    elif isinstance(value, str):
                                        message = value
                                    else:
                                        data = value
                        else:
                            data = response

                        if code < 100 or code >= 600:
                            utils.logging.log("The returning HTTP status code doesn't seem to be a standard status code: {code}".format(
                                code=code), level=utils.logging.LogLevels.WARNING)

                        if not self.endpoint.json:
                            final = flask.Response(response=data, status=code)

                            try:
                                if error:
                                    final.headers["X-NASSE-ERROR"] = str(error)

                                if config.Mode.DEBUG:
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
                            except Exception:
                                pass
                        else:
                            result = {
                                "success": error is None,
                                "error": error,
                                "message": message,
                                "data": {}
                            }
                            if utils.annotations.is_unpackable(data):
                                # data: {"username": "someone", "token": "something"}
                                result["data"] = dict(data)
                            elif isinstance(data, bytes):
                                # data: bytes data, raw file content
                                result["data"]["base64"] = base64.b64encode(data).decode("utf-8")
                            elif hasattr(data, "read") and hasattr(data, "tell") and hasattr(data, "seek"):
                                # a file object
                                position = data.tell()  # storing the current position
                                content = data.read()  # read it (place the cursor at the end)
                                # go back to the original position
                                data.seek(position)
                                if "b" in data.mode:  # if binary mode
                                    result["data"]["base64"] = base64.b64encode(content).decode("utf-8")  # base64 encode the result
                                else:
                                    result["data"]["content"] = str(content)
                            elif isinstance(data, str):
                                # data: "Hello World"
                                result["data"]["string"] = data
                            elif isinstance(data, typing.Iterable):
                                # data: ["an", "array", "of", "element"] | ("an", "array", ...) | etc.
                                result["data"]["array"] = list(data)
                            elif data is None:
                                result["data"]["content"] = None
                            else:
                                # data: typing.Any (but json does not support arbitrary content)
                                utils.logging.log(
                                    "Element of type <{type}> is not supported by JSON and will be converted to `str`".format(type=data.__class__.__name__), level=utils.logging.LogLevels.WARNING)
                                result["data"]["content"] = str(data)
                except Exception as e:
                    # from traceback import print_exc; print_exc()
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
                    message, error, code = exception_to_response(e)
                    result = {
                        "success": False,
                        "error": error,
                        "message": message,
                        "data": {}
                    }

                if self.endpoint.json:
                    CALL_STACK, LOG_STACK = STACK.stop()
                    if config.Mode.DEBUG:
                        result["debug"] = {
                            "time": {
                                "global": global_timer.stop(),
                                "verification": verification_timer.time if verification_timer is not None else None,
                                "authentication": authentication_timer.time if authentication_timer is not None else None,
                                "processing": processing_timer.time if processing_timer is not None else None,
                                "formatting": formatting_timer.stop() if formatting_timer is not None else None
                            },
                            "ip": flask.g.request.client_ip if isinstance(flask.g.request, request.Request) else utils.ip.get_ip(),
                            "headers": dict(flask.g.request.headers),
                            "values": dict(flask.g.request.values),
                            "domain": flask.g.request.host,
                            "logs": LOG_STACK,
                            "call_stack": ["pass the 'call_stack' parameter to get the call stack"]
                        }

                        if "call_stack" in flask.g.request.values:
                            result["debug"]["call_stack"] = [frame.as_dict()
                                                             for frame in CALL_STACK]

                    minify = utils.boolean.to_bool(flask.g.request.values.get("minify", False))

                    content_type = "application/json"
                    if utils.sanitize.remove_spaces(flask.g.request.values.get("format", "json")).lower() in {"xml", "html"}:
                        body = utils.xml.encode(data=result, minify=minify)
                        content_type = "application/xml"
                    else:
                        body = (utils.json.minified_encoder if minify else utils.json.encoder).encode(result)

                    final = flask.Response(body, status=code)
                    final.headers["Content-Type"] = content_type

            try:
                final
            except Exception:
                # final is not defined, meaning that the exception was raised before the response was created
                final = flask.Response(None, status=code)

                try:
                    if error:
                        final.headers["X-NASSE-ERROR"] = str(error)

                    if config.Mode.DEBUG:
                        final.headers["X-NASSE-TIME-GLOBAL"] = str(global_timer.stop())
                        final.headers["X-NASSE-TIME-VERIFICATION"] = str(verification_timer.time) if verification_timer is not None else "N/A"
                        final.headers["X-NASSE-TIME-AUTHENTICATION"] = str(authentication_timer.time) if authentication_timer is not None else "N/A"
                        final.headers["X-NASSE-TIME-PROCESSING"] = str(processing_timer.time) if processing_timer is not None else "N/A"
                        final.headers["X-NASSE-TIME-FORMATTING"] = str(formatting_timer.stop()) if formatting_timer is not None else "N/A"
                except Exception:
                    pass

            try:
                flask.g.request
            except Exception:
                flask.g.request = flask.request
            try:
                cookies
            except Exception:
                cookies = []
            try:
                headers
            except Exception:
                headers = {}

            # final is now defined
            for cookie in cookies:
                # 'cookie' should be a ResponseCookie
                final.headers.add("Set-Cookie", cookie.dumps())

            for key, value in headers.items():
                final.headers.add(str(key), str(value))

            try:
                size = sys.getsizeof(final.data)
                if isinstance(flask.g.request, request.Request):
                    path = flask.g.request.nasse_endpoint.path
                    ip = flask.g.request.client_ip
                    method = flask.g.request.method
                else:
                    path = flask.g.request.path
                    ip = utils.ip.get_ip()
                    method = str(flask.g.request.method).upper()
                if size < 500000:
                    color = utils.logging.Colors.green
                elif size < 1000000:
                    color = utils.logging.Colors.yellow
                else:
                    color = utils.logging.Colors.magenta
                utils.logging.log("← Sending back {color}{size}{normal} bytes of data to {ip} following {blue}{method} {path}{normal}".format(
                    color=color,
                    size=size,
                    normal=utils.logging.Colors.normal,
                    ip=ip,
                    method=method,
                    path=path,
                    blue=utils.logging.Colors.blue
                ))
            except Exception:
                pass

            return final
