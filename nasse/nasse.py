"""
Nasse

© Anime no Sekai — 2021
"""
import logging
import os
import pathlib
import sys
import threading
import typing
import urllib.parse

import flask
import rich.status
import rich.progress
import watchdog.events
import watchdog.observers

from nasse import config, docs, models, receive, request, utils
from nasse.docs.localization.base import Localization
from nasse.response import exception_to_response
from nasse.servers.flask import Flask


class FileEventHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, callback: typing.Callable, watch: typing.List[pathlib.Path], ignore: typing.List[pathlib.Path], config: config.NasseConfig = None) -> None:
        super().__init__()
        self.config = config or config.NasseConfig()
        self.callback = callback
        self.watch = [str(file) for file in watch]
        self.ignore = [str(file) for file in ignore]

    def on_modified(self, event):
        src_path = str(pathlib.Path(str(event.src_path)).resolve())
        if src_path not in self.watch or src_path in self.ignore:
            return
        self.config.logger.log("{path} modified".format(path=src_path))
        self.callback()


class Nasse():
    def __init__(self, name: str = None, flask_options: dict = None, *args, **kwargs) -> None:
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
        `name`: str, default = None
            The name of the server \n
            If 'name' is None, the name will be implied by the directory name
        `cors`: str | bool | Iterable, default = False
            The Cross-Origin Resource Sharing (CORS) rules for the server \n
            'cors' as a string represents the allowed `Origin` \n
            'cors' as a boolean value respresents `*` when True, no CORS rules (no `Access-Control-Allow-Origin` header set) when False \n
            'cors' as an iterable represents a list of allowed `Origin`s
        `max_body_size`: int, default = 10^9
            The maximum size/length of the request \n
            Setting this as None is dangerous as it will not perform any content size/length check
        """
        self.config = config.NasseConfig(app=name or "Nasse", *args, **kwargs)
        self.config.logger.config = self.config
        utils.logging.logger = self.config.logger

        if self.config.debug:
            threading.settrace(utils.logging._generate_trace(self.config))

        if isinstance(self.config.account_management, type):
            self.config.account_management = self.config.account_management()

        self.flask = flask.Flask(self.config.app, **(flask_options or {}))

        self.endpoints = {}

        # security
        self.flask.config["MAX_CONTENT_LENGTH"] = int(self.config.max_request_size) if self.config.max_request_size is not None else None

        # events
        self.flask.before_request(lambda: self.before_request())
        # the lambda function, acting as a proxy between the real after_request function is here to let the user change the function as wanted
        self.flask.after_request(lambda response: self.after_request(response))

        self.flask.register_error_handler(Exception, self.handle_exception)

        if self.config.compress:
            import flask_compress
            flask_compress.Compress(self.flask)

        logging.getLogger('werkzeug').disabled = True
        self.flask.logger.disabled = True

        # on debug
        self._observer = None

    def __repr__(self) -> str:
        return "Nasse({name})".format(name=self.config.app)

    def route(self,
              path: str = utils.annotations.Default(""),
              endpoint: models.Endpoint = None,
              flask_options: dict = None, **kwargs):
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
            If needed, extra options to give to flask.Flask
        `**kwargs`
            The same options that will be passed to nasse.models.Endpoint to create the new endpoint. \n
            Refer to `nasse.models.Endpoint` docs for more information on what to give here.
        """
        flask_options = dict(flask_options or {})

        def decorator(f):
            results = dict(endpoint or {})
            # we don't path to overwrite the default behavior
            results.pop("path", None)
            results["path"] = path
            results.update(kwargs)
            results["handler"] = f
            new_endpoint = models.Endpoint(**results)
            flask_options["methods"] = new_endpoint.methods if "*" not in new_endpoint.methods else utils.types.HTTPMethod.ACCEPTED
            self.flask.add_url_rule(new_endpoint.path, flask_options.pop(
                "endpoint", None), receive.Receive(self, new_endpoint), **flask_options)
            self.endpoints[new_endpoint.path] = new_endpoint
            return new_endpoint
        return decorator

    def run(self, host: str = None, port: typing.Union[int, str] = None, server: typing.Type[Flask] = Flask, watch: typing.List[str] = ["**/*.py"], ignore: typing.List[str] = [], *args, **kwargs):
        """
        Runs the application by binding to an address and answering to clients.
        """
        columns = (rich.progress.TextColumn("[progress.description]{task.description}"),
                   rich.progress.TimeElapsedColumn())
        with rich.progress.Progress(rich.progress.SpinnerColumn(),
                                    *columns,
                                    transient=True) as progress:
            main_task = progress.add_task("Setting up the environment", total=None)

            if host is not None:
                self.config.host = host
            if port is not None:
                self.config.port = int(port)
            if "debug" in kwargs:
                self.config.debug = kwargs["debug"]

            try:
                if self.config.debug:
                    self.config.logger.log("DEBUG MODE IS ENABLED", level=utils.logging.LoggingLevel.WARNING)
                    watching = []
                    ignoring = []
                    for storage, data in [(watching, watch), (ignoring, ignore)]:
                        for file in data:
                            file = str(file)
                            path = pathlib.Path(file)
                            if path.is_file():
                                storage.append(path.resolve())
                            elif path.is_dir():
                                storage.extend(child.resolve() for child in path.iterdir())
                            else:
                                storage.extend(child.resolve() for child in pathlib.Path().glob(file))
                    self._observer = watchdog.observers.Observer()
                    self._observer.schedule(FileEventHandler(callback=self.restart, watch=watching, ignore=ignoring), ".", recursive=True)
                    self._observer.start()
            except Exception:
                self.config.logger.log("Couldn't set up the file changes watcher", level=utils.logging.LoggingLevel.WARNING)

            self.instance = server(app=self, config=self.config)
            self.config.logger.log("🍡 Press Ctrl+C to quit")
            self.config.logger.log("🎏 Binding to {{magenta}}{host}:{port}{{normal}}"
                                   .format(host=self.config.host,
                                           port=self.config.port))
            # progress.columns = (rich.progress.SpinnerColumn(spinner_name="earth"), *columns)
            spinner = rich.progress.SpinnerColumn(spinner_name="simpleDotsScrolling", style="gray")
            # spinner.spinner.frames = ["・　　", "・・　", "・・・", "　・・", "　　・", "　　　"]
            progress.columns = (spinner, *columns)
            progress.update(main_task, description="Running on {host}:{port} —".format(host=self.config.host, port=self.config.port))
            self.instance.run(*args, **kwargs)

    def restart(self):
        """Restarts the current python process"""
        self.config.logger.log("Restarting... 🎐")
        if self._observer:
            self.config.logger.log("Waiting for watchdog to terminate", level=utils.logging.LoggingLevel.DEBUG)
            try:
                self._observer.stop()
                self._observer.join()
            except Exception:
                pass
        self.config.logger.log("Stopping the server instance")
        self.instance.stop()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def handle_exception(self, e):
        """
        Handles exception for flask.Flask
        """
        try:
            try:
                message, error, code = exception_to_response(e)
            except Exception:
                message, error, code = "An error occured on the server", "SERVER_ERROR", 500
            result = {"success": False, "message": message, "error": error, "data": {}}
            content_type = "application/json"
            try:
                if utils.sanitize.remove_spaces(flask.request.values.get("format", "json")).lower() in {"xml", "html"}:
                    body = utils.xml.encode(data=result, minify=True)
                    content_type = "application/xml"
                raise ValueError("Not XML")
            except Exception:
                body = utils.json.minified_encoder.encode(result)
            return flask.Response(response=body, status=code, content_type=content_type)
        except Exception:
            return flask.Response(response='{"success": false, "message": "An error occured on the server", "error": "SERVER_ERROR", "data": {}', status=500, content_type="application/json")

    def before_request(self):
        """
        Internal function called when before receiving a response

        Might be useful to check things (like a database) before the request

        You won't need this function to perform validation if you are consistently
        and rightfully documenting your endpoints as Nasse will take care of this for you.
        """
        return

    def after_request(self, response: flask.Response):
        """
        Internal function called before sending back a response
        It applies multiple security headers to ensure HTTPS, CORS, etc.

        Parameters
        -----------
        `response`: flask.flask.Response
            The response to send back

        Returns
        --------
        `flask.Response`:
            The response to send
        """
        try:
            # Ensuring HTTPS (for a year)
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

            # Managing CORS
            # Allowing the right methods
            try:
                if flask.request.method.upper() == "OPTIONS":
                    current_endpoint = self.endpoints.get(
                        flask.request.url_rule.rule, None)
                    if current_endpoint is not None:
                        try:
                            response.headers["Access-Control-Allow-Methods"] = ",".join(current_endpoint.methods)
                        except Exception:
                            from traceback import print_exc
                            print_exc()
                            self.config.logger.log("An error occured while setting the Access-Control-Allow-Methods header",
                                                   level=utils.logging.LoggingLevel.WARNING)
                        try:
                            requested_headers = [header.lower() for header in utils.sanitize.remove_spaces(
                                flask.request.headers.get("Access-Control-Request-Headers", "")).split(",")]
                            endpoint_headers = [header.name.lower() for header in current_endpoint.headers]

                            # login_rules = current_endpoint.login.get(flask.request.method.upper(), current_endpoint.login.get("*", None))
                            # if login_rules is not None and not login_rules.no_login:
                            #     endpoint_headers.append("authorization")
                            endpoint_headers.append("authorization")

                            response.headers["Access-Control-Allow-Headers"] = ",".join(
                                (header for header in requested_headers if header in endpoint_headers))
                        except Exception:
                            from traceback import print_exc
                            print_exc()
                            self.config.logger.log("An error occured while setting the Access-Control-Allow-Headers header",
                                                   level=utils.logging.LoggingLevel.WARNING)
                    else:
                        self.config.logger.log("We couldn't verify the current endpoint informations on an OPTIONS request",
                                               level=utils.logging.LoggingLevel.WARNING)
                    response.headers["Access-Control-Max-Age"] = 86400
            except Exception:
                self.config.logger.log("An error occured while setting some CORS headers", level=utils.logging.LoggingLevel.WARNING)

            # Allowing the right origins
            if self.config.cors:
                if "*" in self.config.cors:
                    origin = flask.request.environ.get("HTTP_ORIGIN", None)
                    if origin is not None:
                        response.headers["Vary"] = "Origin"
                        response.headers["Access-Control-Allow-Origin"] = origin
                    else:
                        response.headers["Access-Control-Allow-Origin"] = "*"
                else:
                    response.headers["Vary"] = "Origin"
                    request_origin = flask.request.environ.get(
                        "HTTP_ORIGIN", None)
                    if request_origin in self.config.cors:
                        response.headers["Access-Control-Allow-Origin"] = request_origin
                    else:
                        response.headers["Access-Control-Allow-Origin"] = self.config.cors[0]
            # Might need to allow the right headers
            # ...

            response.headers["Server"] = "Nasse/{version} ({name})".format(
                version=config.GLOBAL_CONFIG_ARE_A_THING_OF_THE_PAST.VERSION, name=self.name)

        except Exception:
            # would be bad if the `after_request` function raises an exception, especially when used as the `teardown_request`
            pass

        return response

    def make_docs(self, base_dir: typing.Union[pathlib.Path, str] = None, curl: bool = True, javascript: bool = True, python: bool = True, localization: Localization = Localization):
        """
        Creates the documentation for your API/Server

        Parameters
        ----------
        base_dir: str | Path
            The path where the docs will be outputted \n
            This shouldn't be the path to the Endpoints.md file, but rather a directory where
            the `postman` docs and the Endpoints.md file will be outputted
        curl: bool
            Whether or not to generate the curl examples
        javascript: bool
            Whether or not to generate the javascript examples
        python: bool
            Whether or not to generate the python examples
        """
        with rich.progress.Progress(rich.progress.SpinnerColumn(),
                                    *rich.progress.Progress.get_default_columns()) as progress:
            main_task = progress.add_task("Creating the API Reference Documentation", total=5)
            self.config.logger.log("Creating the API Reference Documentation", level=utils.logging.LoggingLevel.HIDDEN)

            docs_path = pathlib.Path(base_dir or pathlib.Path() / "docs")
            if not docs_path.is_dir():
                docs_path.mkdir()

            postman_path = docs_path / "postman"
            if not postman_path.is_dir():
                postman_path.mkdir()

            sections_path = docs_path / localization.sections
            if not sections_path.is_dir():
                sections_path.mkdir()
            progress.advance(main_task)

            # Initializing the resulting string by prepending the header
            result = localization.getting_started_header.format(name=self.config.app, id=self.config.id)

            result += "## {localization__index}\n\n".format(localization__index=localization.index)

            # Sorting the sections alphabetically
            sections = sorted({endpoint.section for endpoint in self.endpoints.values()})

            # Getting the endpoints for each section
            sections_registry = {}
            for section in sections:
                for endpoint in self.endpoints.values():
                    if endpoint.section == section:
                        try:
                            sections_registry[section].append(endpoint)
                        except Exception:
                            sections_registry[section] = [endpoint]

            progress.advance(main_task)

            headers_registry = []

            for section in sections_registry:
                current_link = docs.header.header_link(section, headers_registry)
                result += "- [{section}](./{localization__sections}/{section_url}.md#{link})\n".format(section=section,
                                                                                                       localization__sections=urllib.parse.quote(
                                                                                                           localization.sections, safe=''),
                                                                                                       section_url=section.replace(" ", "%20"),
                                                                                                       link=current_link)

                result += "\n".join(["  - [{endpoint}](./{localization__sections}/{section}.md#{link})".format(
                    endpoint=endpoint.name,
                    localization__sections=urllib.parse.quote(localization.sections, safe=""),
                    section=section.replace(" ", "%20"),
                    link=docs.header.header_link(endpoint.name, headers_registry)) for endpoint in sections_registry[section]]
                )
                result += "\n"

            progress.advance(main_task)

            with open(docs_path / "{localization__getting_started}.md".format(localization__getting_started=localization.getting_started), "w", encoding="utf8") as out:
                out.write(result)

            progress.advance(main_task)

            # Dumping all of the docs and creating the Postman Data
            for section in sections_registry:
                result = localization.section_header.format(name=section)
                # result += '''\n## {section}\n'''.format(section=section)
                result += "\n".join([docs.markdown.make_docs(endpoint, curl=curl, javascript=javascript, python=python, localization=localization)
                                    for endpoint in sections_registry[section]])
                with open(sections_path / "{section}.md".format(section=section), "w", encoding="utf-8") as out:
                    out.write(result)

                result = docs.postman.create_postman_data(self, section, sections_registry[section], localization=localization)
                with open(postman_path / "{section}.postman_collection.utils.json".format(section=section), "w", encoding="utf-8") as out:
                    out.write(utils.json.minified_encoder.encode(result))
            progress.advance(main_task)
