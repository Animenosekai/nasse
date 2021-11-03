"""
Nasse v1.0.0 (Stable)

© Anime no Sekai — 2021
"""
import logging
import os
import sys
import threading
from multiprocessing import cpu_count
from pathlib import Path
from typing import Callable, Iterable, Union
from urllib.parse import urlparse

import gunicorn
import gunicorn.app.base
from flask import Flask, Response, g
from flask import request as flask_request
from gunicorn.arbiter import Arbiter
from nasse import models, receive, request
from nasse.config import Enums, General, Mode
from nasse.utils import xml, json
from nasse.docs import markdown
from nasse.docs.header import DOCS_HEADER, header_link
from nasse.docs.postman import create_postman_data
from nasse.response import exception_to_response
from nasse.utils.args import Args
from nasse.utils.logging import LogLevels, add_to_call_stack, log
from nasse.utils.sanitize import alphabetic, remove_spaces
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable) -> None:
        super().__init__()
        self.callback = callback

    def on_modified(self, event):
        src_path = str(event.src_path)
        if not any([src_path.endswith(extension) for extension in (".py", ".html", ".js", ".css")]):
            return
        log("{path} modified".format(path=src_path))
        self.callback()


class GunicornServer(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options: dict = None):
        self.options = {
            'bind': '{host}:{port}'.format(host=General.HOST, port=Args.get(("-p", "--port"), 5000)),
            'workers': 2 * cpu_count() + 1,
            'capture_output': False,
            'proc_name': app.id,
            'preload_app': True,
            'worker_class': General.WORKER_CLASS,
            'threads': 2 * cpu_count() + 1,
            'loglevel': 'error',
            # would be painful to wait 30 seconds on each reload
            'graceful_timeout': 5 if Mode.DEBUG else 20
        }
        self.options.update(options or {})
        self.application = app.flask
        formatting = {}
        if "{version}" in General.SERVER_HEADER:
            formatting["version"] = General.VERSION
        if "{app}" in General.SERVER_HEADER:
            formatting["app"] = app.id
        gunicorn.SERVER_SOFTWARE = General.SERVER_HEADER.format(**formatting)
        gunicorn.SERVER = General.SERVER_HEADER.format(**formatting)
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


class Nasse():
    _observer = None
    _arbiter = None

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
        self.flask.before_request(lambda: self.before_request())
        # the lambda function, acting as a proxy between the real after_request function is here to let the user change the function as wanted
        self.flask.after_request(lambda response: self.after_request(response))

        self.flask.register_error_handler(Exception, self.handle_exception)

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

    def run(self, host: str = None, port: Union[int, str] = None, **kwargs):
        """
        Runs the application on a local development server.

        Do not use `run()` in a production setting **for now**. It is not intended to
        meet security and performance requirements for a production server.
        """
        log("Running the server ✨", level=LogLevels.INFO)
        parameters = {
            "bind": "{host}:{port}".format(host=host or General.HOST, port=port or Args.get(("-p", "--port"), 5000))
        }
        parameters.update(kwargs)
        if Mode.DEBUG:
            log("DEBUG MODE IS ENABLED", level=LogLevels.WARNING)
            self._observer = Observer()
            self._observer.schedule(FileEventHandler(
                self.restart), ".", recursive=True)
            self._observer.start()
        self._arbiter = Arbiter(GunicornServer(self, options=parameters))
        self._arbiter.run()

        # self.flask.run(host=host, port=port, debug=debug, **kwargs)

    def restart(self):
        """Restarts the current python process"""
        log("Restarting...", level=LogLevels.INFO)
        if self._observer:
            log("Waiting for watchdog to terminate")
            try:
                self._observer.stop()
                self._observer.join()
            except Exception:
                pass
        if self._arbiter:
            log("Waiting for workers to terminate")
            self._arbiter.stop()
        os.execv(sys.executable, ['python'] + sys.argv)

    def handle_exception(self, e):
        """
        Handles exception for Flask
        """
        try:
            try:
                data, error, code = exception_to_response(e)
            except Exception:
                data, error, code = "An error occured on the server", "SERVER_ERROR", 500
            result = {"success": False, "error": error,
                      "data": {"message": data}}
            try:
                if remove_spaces(g.request.values.get("format", "json")).lower() in {"xml", "html"}:
                    body = xml.encode(data=result, minify=True)
                raise ValueError("Not XML")
            except Exception:
                body = json.minified_encoder.encode(result)
            return Response(response=body, status=code)
        except Exception:
            return Response(response='{"success": false, "error": "SERVER_ERROR", "data": {"message": "An error occured on the server"}', status=500)

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

    def make_docs(self, base_dir: Union[Path, str] = None):
        """
        Creates the documentation for your API/Server

        Parameters
        ----------
            base_dir: str | Path
                The path where the docs will be outputted \n
                This shouldn't be the path to the Endpoints.md file, but rather a directory where
                the `postman` docs and the Endpoints.md file will be outputted
        """
        log("Creating the API Reference Documentation")
        docs_path = Path(base_dir or Path() / "docs")
        if not docs_path.is_dir():
            docs_path.mkdir()

        postman_path = docs_path / "postman"
        if not postman_path.is_dir():
            postman_path.mkdir()

        # Initializing the resulting string by prepending the header
        result = DOCS_HEADER.format(name=self.name, id=self.id)

        result += "\n## Index\n"

        # Sorting the sections alphabetically
        sections = sorted(set(
            [endpoint.section for endpoint in self.endpoints.values()]))

        # Getting the endpoints for each section
        sections_registry: dict[str, list[models.Endpoint]] = {}
        for section in sections:
            for endpoint in self.endpoints.values():
                if endpoint.section == section:
                    try:
                        sections_registry[section].append(endpoint)
                    except:
                        sections_registry[section] = [endpoint]

        headers_registry = []

        for section in sections_registry:
            current_link = header_link(section, headers_registry)
            result += "- [{section}](#{link})\n".format(
                section=section, link=current_link)
            current_link = header_link(endpoint.name, headers_registry)

            result += "\n".join(
                ["  - [{endpoint}](#{link})".format(endpoint=endpoint.name, link=header_link(endpoint.name, headers_registry)) for endpoint in sections_registry[section]])
            result += "\n"

        # Dumping all of the docs and creating the Postman Data
        for section in sections_registry:
            postman_results = create_postman_data(
                self, section, sections_registry[section])
            with open(postman_path / "{section}.postman_collection.json".format(section=section), "w") as postman_output:
                postman_output.write(json.minified_encoder.encode(postman_results))

            result += f'''

## {section}
'''
            result += "\n[Return to the Index](#index)\n".join(
                [markdown.make_docs(endpoint) for endpoint in sections_registry[section]])

        with open(docs_path / "Endpoints.md", "w", encoding="utf8") as out:
            out.write(result)


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
