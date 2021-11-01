"""
Nasse v1.0.0 (Stable)

© Anime no Sekai — 2021
"""
import logging
import threading
from typing import Iterable, Union
from urllib.parse import urlparse

from flask import Flask, Response
from flask import request as flask_request

from nasse import models, receive, request
from nasse.config import Enums, General, Mode
from nasse.utils.logging import add_to_call_stack
from nasse.utils.sanitize import alphabetic, remove_spaces


class Nasse():
    def __init__(self, name: str = None, id: str = None, account_management: models.AccountManagement = None, cors: Union[str, bool, Iterable] = True, max_request_size: int = 1e+9, compress: bool = True, *args, **kwargs) -> None:
        """
        # A Nasse web server instance

        Examples
        ---------
        >>> from nasse import Nasse
        >>> app = Nasse()

        ...is the most minimalist usage, but we obviously recommend customizing the parameters:

        >>> app = Nasse(name="New Server", cors=["https://new-server.com", "https://beta-new-server.com"])

        Parameters
        -----------
            `name`: str, defaults = None
                The name of the server \n
                If 'name' is None, the name will be implied by the directory name
            `cors`: str | bool | Iterable, defaults = False
                The Cross-Origin Resource Sharing (CORS) rules for the server \n
                'cors' as a string represents the allowed `Origin` \n
                'cors' as a boolean value respresents `*` when True, no CORS rules (no `Access-Control-Allow-Origin` header set) when False \n
                'cors' as an iterable represents a list of allowed `Origin`s
            `max_body_size`: int, defaults = 10^9
                The maximum size/length of the request \n
                Setting this as None is dangerous as it will not perform any content size/length check
        """
        if Mode.DEBUG:
            threading.settrace(
                General.CALL_TRACE_RECEIVER or add_to_call_stack)
        self.name = str(name or General.BASE_DIR.name or "Nasse")
        self.id = str(id or alphabetic(self.name).lower())

        self.account_management = account_management

        self.flask = Flask(self.name, *args, **kwargs)

        if isinstance(cors, str):
            rule = remove_spaces(cors)
            parsed = urlparse(rule)
            scheme = parsed.scheme or "https"
            rule = '{scheme}://{netloc}'.format(
                scheme=scheme, netloc=parsed.netloc) if rule != "*" else "*"
            self.cors = [rule]
        elif isinstance(cors, bool):
            self.cors = ["*"] if cors else []
        else:
            self.cors = []
            for rule in cors:
                rule = remove_spaces(rule)
                parsed = urlparse(rule)
                scheme = parsed.scheme or "https"
                rule = '{scheme}://{netloc}'.format(
                    scheme=scheme, netloc=parsed.netloc) if rule != "*" else "*"
                self.cors.append(rule)

        self.endpoints: dict[str, models.Endpoint] = {}

        # security
        self.flask.config["MAX_CONTENT_LENGTH"] = int(
            max_request_size) if max_request_size is not None else None

        # events
        self.flask.before_request_funcs.setdefault(
            None, []).append(self.before_request)
        self.flask.after_request_funcs.setdefault(
            None, []).append(self.after_request)

        if compress:
            import flask_compress
            flask_compress.Compress(self.flask)

        logging.getLogger('werkzeug').disabled = True
        self.flask.logger.disabled = True

    def __repr__(self) -> str:
        return "Nasse({name})".format(name=self.name)

    def route(self, endpoint: models.Endpoint = None, flask_options: dict = None, **kwargs):
        """
        # A decorator to register a new endpoint

        Can be used like so:
        >>> from nasse import Nasse, Param
        >>> app = Nasse()
        >>>
        >>> @app.route(path="/hello", params=Param(name="username", description="the person welcomed"))
        ... def hello(params: dict):
        ...     if "username" in params:
        ...         return f"Hello {params['username']}"
        ...     return "Hello world"

        Parameters
        -----------
            `endpoint`: nasse.models.Endpoint
                A base endpoint object. Other given values will overwrite the values from this Endpoint object.
            `flask_options`: dict
                If needed, extra options to give to Flask
            `**kwargs`
                The same options that will be passed to nasse.models.Endpoint to create the new endpoint. \n
                Refer to `nasse.models.Endpoint` docs for more information on what to give here.
        """
        flask_options = flask_options or {}

        def decorator(f):
            results = dict(endpoint or {})
            results.update(kwargs)
            results["handler"] = f
            new_endpoint = models.Endpoint(**results)
            flask_options["methods"] = new_endpoint.methods if "*" not in new_endpoint.methods else Enums.Conventions.HTTP_METHODS
            self.flask.add_url_rule(new_endpoint.path, flask_options.pop(
                "endpoint", None), receive.Receive(self, new_endpoint), **flask_options)
            self.endpoints[new_endpoint.path] = new_endpoint
            return new_endpoint
        return decorator

    def run(self, host: str = None, port: Union[int, str] = None, debug: bool = None, **kwargs):
        """
        Runs the application on a local development server.

        Do not use `run()` in a production setting **for now**. It is not intended to
        meet security and performance requirements for a production server.
        """
        self.flask.run(host=host, port=port, debug=debug, **kwargs)

    def before_request(self):
        """
        Internal function called when before receiving a response

        Might be useful to check things (like a database) before the request

        You won't need this function to perform validation if you are consistently
        and rightfully documenting your endpoints as Nasse will take care of this for you.
        """
        return

    def after_request(self, response: Response):
        """
        Internal function called before sending back a response
        It applies multiple security headers to ensure HTTPS, CORS, etc.

        Parameters
        -----------
            `response`: flask.Response
                The response to send back

        Returns
        --------
            `Response`:
                The response to send
        """
        try:
            # Ensuring HTTPS (for a year)
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

            # Managing CORS
            # Allowing the right methods
            if flask_request.method.upper() == "OPTIONS":
                current_endpoint = self.endpoints.get(
                    request.url_rule.rule, None)
                if current_endpoint is not None:
                    response.headers["Access-Control-Allow-Methods"] = ", ".join(
                        current_endpoint.methods)
                    if Mode.PRODUCTION:
                        response.headers["Access-Control-Max-Age"] = 86400
            # Allowing the right origins
            if self.cors:
                if "*" in self.cors:
                    origin = flask_request.environ.get("HTTP_ORIGIN", None)
                    if origin is not None:
                        response.headers["Vary"] = "Origin"
                        response.headers["Access-Control-Allow-Origin"] = origin
                else:
                    response.headers["Vary"] = "Origin"
                    request_origin = flask_request.environ.get(
                        "HTTP_ORIGIN", None)
                    if request_origin is self.cors:
                        response.headers["Access-Control-Allow-Origin"] = request_origin
                    else:
                        response.headers["Access-Control-Allow-Origin"] = self.cors[0]

            # Might need to allow the right headers
            # ...

            response.headers["Server"] = "Nasse/{version} ({name})".format(
                version=General.VERSION, name=self.name)

        except Exception:
            # would be bad if the `after_request` function raises an exception, especially when used as the `teardown_request`
            pass

        return response


############
# TO ADD

# finalize_request          --
# full_dispatch_request       |     def event()...
# got_first_request         --

# errorhandler              --
# handle_exception            |
# handle_http_exception       |     def handle_exception...
# handle_url_build_error      |
# handle_user_exception     --

# json_decoder              --      JSON.decode
# json_encoder              --      JSON.encode

# run                        |      def run...
