"""
Nasse

© Anime no Sekai — 2023
"""
import logging
import os
import pathlib
import sys
import threading
import typing
import urllib.parse
import dataclasses

import flask
import rich.progress
import rich.status
import watchdog.events
import watchdog.observers

from nasse import config, docs, models, receive, request, utils
from nasse.config import NasseConfig
from nasse.localization.base import Localization
from nasse.response import exception_to_response
from nasse.servers import ServerBackend
from nasse.servers.flask import Flask


class FileEventHandler(watchdog.events.FileSystemEventHandler):
    """An internal file event handler for the debug mode"""

    def __init__(self, callback: typing.Callable, watch: typing.List[pathlib.Path], ignore: typing.List[pathlib.Path], config: NasseConfig = None) -> None:
        super().__init__()
        self.config = config or NasseConfig()
        self.callback = callback
        self.watch = [str(file) for file in watch]
        self.ignore = [str(file) for file in ignore]

    def on_modified(self, event):
        src_path = str(pathlib.Path(str(event.src_path)).resolve())
        if src_path not in self.watch or src_path in self.ignore:
            return
        self.config.logger.log("{path} modified".format(path=src_path))
        self.callback()


class Nasse:
    """The Nasse web server object"""

    def __init__(self,
                 name: typing.Optional[str] = None,
                 config: typing.Optional[NasseConfig] = None,
                 flask_options: typing.Optional[dict] = None,
                 *args, **kwargs) -> None:
        """
        # Nasse

        Examples
        ---------
        >>> from nasse import Nasse
        >>> app = Nasse()

        ...is the most minimalist usage, but we obviously recommend customizing the parameters:

        >>> app = Nasse(name="New Server", cors=["https://new-server.com", "https://beta-new-server.com"])

        Parameters
        -----------
        name: str, default = None
            Defines the name of the server
        config: NasseConfig, default = None
            A NasseConfig object, with all of the configuration for the server
        flask_options: dict, default = None
            A dictionary with the options to pass to Flask when creating the Flask instance
        *args
            Arguments to give to NasseConfig
        **kwargs
            Keyword arguments to give to NasseConfig
        """
        if isinstance(name, NasseConfig):
            config = name
            name = None
        if config:
            config_kwargs = config.__dict__
            config_kwargs.update(kwargs)
            config_kwargs["name"] = name or config_kwargs.get("app", "Nasse")
            # config_kwargs.pop("VERSION", None)
            self.config = NasseConfig(*args, **config_kwargs)
        else:
            self.config = NasseConfig(name=name or "Nasse", *args, **kwargs)

        self.config.logger.config = self.config
        utils.logging.logger = self.config.logger

        if self.config.debug:
            threading.settrace(utils.logging._generate_trace(self.config))

        if isinstance(self.config.account_management, type):
            self.config.account_management = self.config.account_management()

        self.flask = flask.Flask(self.config.name, **(flask_options or {}))

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
        return "Nasse({name})".format(name=self.config.name)

    @property
    def logger(self) -> utils.logging.Logger:
        return self.config.logger

    def log(self, *msg, **kwargs):
        return self.logger.log(*msg, **kwargs)

    def route(self,
              path: typing.Optional[typing.Union[typing.Callable, str]] = None,

              name: str = "",
              category: str = "",
              sub_category: str = "",
              description: models.Types.MethodVariant[str] = None,
              base_dir: typing.Union[pathlib.Path, str, None] = None,
              endpoint: typing.Optional[typing.Union[models.Endpoint, typing.Mapping]] = None,

              # Request,
              methods: models.Types.OptionalIterable[models.Types.Method.Any] = "*",
              login: models.Types.MethodVariant[models.Types.OptionalIterable[models.Login]] = None,

              # User Sent,
              parameters: models.Types.MethodVariant[models.Types.OptionalIterable[models.Parameter]] = None,
              headers: models.Types.MethodVariant[models.Types.OptionalIterable[models.Header]] = None,
              cookies: models.Types.MethodVariant[models.Types.OptionalIterable[models.Cookie]] = None,
              dynamics: models.Types.MethodVariant[models.Types.OptionalIterable[models.Dynamic]] = None,

              # Response,
              json: bool = True,
              returns: models.Types.MethodVariant[models.Types.OptionalIterable[models.Return]] = None,
              errors: models.Types.MethodVariant[models.Types.OptionalIterable[models.Error]] = None,
              flask_options: typing.Optional[dict] = None) -> typing.Callable[..., models.Endpoint]:
        """
        Use this function to declare new endpoints

        Examples
        --------
        >>> # Can be used like so:
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
        flask_options: dict
            If needed, extra options to give to flask.Flask
        """
        flask_options = dict(flask_options or {})

        def decorator(handler):
            # if `path` callable, we are in an argument-less decoration
            new_endpoint = models.Endpoint(handler=handler,
                                           name=name,
                                           category=category,
                                           sub_category=sub_category,
                                           description=description,
                                           base_dir=base_dir,
                                           endpoint=endpoint or (path if isinstance(path, models.Endpoint) else None),
                                           path=path if not callable(path) and not isinstance(path, models.Endpoint) else None,
                                           methods=methods,
                                           login=login,
                                           parameters=parameters,
                                           headers=headers,
                                           cookies=cookies,
                                           dynamics=dynamics,
                                           json=json,
                                           returns=returns,
                                           errors=errors)

            try:
                flask_options["methods"] = (new_endpoint.methods
                                            if "*" not in new_endpoint.methods
                                            else typing.get_args(models.Types.Method.Standard))
            except Exception:
                pass

            self.flask.add_url_rule(new_endpoint.path,
                                    flask_options.pop("endpoint", None),
                                    receive.Receive(self, new_endpoint),
                                    **flask_options)

            self.endpoints[new_endpoint.path] = new_endpoint
            return handler

        if callable(path):
            result = decorator(path)  # called without arguments
            return result

        return decorator  # called with arguments

    def run(self,
            host: typing.Optional[str] = None,
            port: typing.Optional[int] = None,
            server: typing.Type[ServerBackend] = Flask,
            watch: typing.Optional[typing.List[str]] = None,
            ignore: typing.Optional[typing.List[str]] = None,
            status: bool = True,
            *args, **kwargs) -> None:
        """
        Runs the application by binding to an address and answering to clients.

        Note: If a `debug` argument is passed to the underlying server backend using `kwargs`, it will be used for `config.debug`

        Parameters
        ----------
        host: str, optional
            The host to run the server on
        port: int, optional
            The port to make the server listen at
        server: Type[ServerBackend], default=Flask
            The server backend to use
        watch: list[str], default=["**/*.py"]
            A list of glob expressions of files to watch for changes in debug mode
        ignore: list[str], optional
            A list of glob expressions of files to ignore changes for in debug mode
        status: bool, default=True
            Whether to show the progress status (time since the server first ran, URL listened, etc.).
            This might come handy in complex environments where you are already using
            a `rich.progress.Progress object, which might conflict.
        """
        if watch is None:
            watch = ["**/*.py"]

        class MockProgress:
            """Replaces the logger"""

            def __overwrite__(self, *args, **kwargs):
                return self

            add_task = __overwrite__
            update = __overwrite__
            __enter__ = __overwrite__
            __exit__ = __overwrite__

        with (rich.progress.Progress(transient=True) if status else MockProgress()) as progress:
            main_task = progress.add_task("Setting up the environment", total=None)

            if host is not None:
                self.config.host = host
            if port is not None:
                self.config.port = int(port)
            if "debug" in kwargs:
                self.config.debug = bool(kwargs["debug"])

            if self.config.debug:
                self.config.logger.warn("DEBUG MODE IS ENABLED")
                # Configuring auto-restart
                try:
                    watching = []
                    ignoring = []
                    for storage, data in [(watching, watch), (ignoring, ignore or [])]:
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
                    self._observer.schedule(FileEventHandler(callback=self.restart, watch=watching,
                                            ignore=ignoring, config=self.config), ".", recursive=True)
                    self._observer.start()
                except Exception as err:
                    self.config.logger.warn(f"Couldn't set up the file changes watcher ({err.__class__.__name__}: {err})")
                # Configuring debug endpoints
                try:
                    def endpoints():
                        """Returns back all of the defined endpoints"""
                        results = {"endpoints": []}
                        for endpoint in self.endpoints.values():
                            # endpoint: models.Endpoint
                            result = {
                                "handler": endpoint.handler.__name__,
                                "name": endpoint.name,
                                "category": endpoint.category,
                                "sub_category": endpoint.sub_category,
                                "description": endpoint.description,
                                "base_dir": endpoint.base_dir,
                                "path": endpoint.path,
                                "methods": endpoint.methods,
                                "json": endpoint.json
                            }
                            for element in ("login", "parameters", "headers", "cookies", "dynamics", "returns", "errors"):
                                result[element] = {key: [dataclasses.asdict(val) for val in value]
                                                   for key, value in getattr(endpoint, element).items()}

                            results["endpoints"].append(result)
                        return 200, results

                    self.route("/@nasse/endpoints",
                               name="Endpoints",
                               category="@Nasse Debug")(endpoints)
                except Exception as err:
                    if self.config.logger:
                        self.config.logger.warn(f"Couldn't set up the debug endpoints ({err.__class__.__name__}: {err})")

            self.instance = server(app=self, config=self.config)

        # Main Loop
        with (rich.progress.Progress(*(rich.progress.TextColumn("[progress.description]{task.description}"),
                                       rich.progress.TextColumn("—"),
                                       rich.progress.TimeElapsedColumn()),
                                     transient=True) if status else MockProgress()) as progress:
            progress.add_task(description=f'🍡 {self.config.name} is running on http://{self.config.host}:{self.config.port}')
            self.config.logger.log("🎏 Press {cyan}Ctrl+C{normal} to quit")
            self.config.logger.log(f"🌍 Binding to {{magenta}}{self.config.host}:{self.config.port}{{normal}}")
            # spinner = rich.progress.SpinnerColumn(spinner_name="simpleDotsScrolling", style="gray")
            # spinner.spinner.frames = ["・　　", "・・　", "・・・", "　・・", "　　・", "　　　"]
            self.instance.run(*args, **kwargs)

    def restart(self):
        """Restarts the current python process"""
        self.config.logger.log("Restarting... 🎐")
        if self._observer:
            self.config.logger.debug("Waiting for watchdog to terminate")
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
        response: flask.flask.Response
            The response to send back

        Returns
        --------
        flask.Response:
            The response to send
        """
        try:
            # Ensuring HTTPS (for a year)
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

            # Managing CORS
            # Allowing the right methods
            try:
                if flask.request.method.upper() == "OPTIONS":
                    current_endpoint = self.endpoints.get(flask.request.url_rule.rule,
                                                          None)
                    if current_endpoint is not None:
                        try:
                            response.headers["Access-Control-Allow-Methods"] = ",".join(current_endpoint.methods)
                        except Exception:
                            from traceback import print_exc
                            print_exc()
                            self.config.logger.warn("An error occured while setting the Access-Control-Allow-Methods header")
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
                            self.config.logger.warn("An error occured while setting the Access-Control-Allow-Headers header")
                    else:
                        self.config.logger.warn("We couldn't verify the current endpoint informations on an OPTIONS request")
                    response.headers["Access-Control-Max-Age"] = 86400
            except Exception:
                self.config.logger.warn("An error occured while setting some CORS headers")

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

            response.headers["Server"] = utils.formatter.format(self.config.server_header, config=self.config)

            # response.headers["Server"] = "Nasse/{version} ({name})".format(version=self.config.VERSION,
            #                                                                name=self.config.name)

        except Exception:
            # would be bad if the `after_request` function raises an exception, especially when used as the `teardown_request`
            pass

        return response

    def make_docs(self, base_dir: typing.Optional[typing.Union[pathlib.Path, str]] = None,
                  curl: bool = True, javascript: bool = True, python: bool = True,
                  localization: typing.Union[typing.Type[Localization], Localization] = Localization):
        """
        Creates the documentation for your API/Server

        Parameters
        ----------
        base_dir: str | Path
            The path where the docs will be outputted.
            This shouldn't be a directory where the `postman` docs and all of the sections will be outputted.
        curl: bool
            Whether or not to generate the curl examples
        javascript: bool
            Whether or not to generate the javascript examples
        python: bool
            Whether or not to generate the python examples
        localization: Localization
            The language for the docs
        """
        with rich.progress.Progress(rich.progress.SpinnerColumn(),
                                    *rich.progress.Progress.get_default_columns(),
                                    transient=True) as progress:
            main_task = progress.add_task("Creating the API Reference Documentation", total=5)
            self.config.logger.hide("Creating the API Reference Documentation")

            docs_path = pathlib.Path(base_dir or pathlib.Path() / "docs")
            docs_path.mkdir(parents=True, exist_ok=True)

            postman_path = docs_path / "Postman"
            postman_path.mkdir(parents=True, exist_ok=True)

            sections_path = docs_path / localization.sections
            sections_path.mkdir(parents=True, exist_ok=True)

            progress.advance(main_task)

            # Initializing the resulting string by prepending the header
            result = localization.getting_started_header.format(name=self.config.name, id=self.config.id)

            result += "## {localization__index}\n\n".format(localization__index=localization.index)

            # Sorting the sections alphabetically
            sections = sorted({endpoint.category for endpoint in self.endpoints.values()})

            # Getting the endpoints for each section
            sections_registry = {}
            for section in sections:
                for endpoint in self.endpoints.values():
                    if endpoint.category == section:
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
                result += "\n".join([docs.markdown.make_docs(endpoint, curl=curl, javascript=javascript, python=python, localization=localization, base_dir=base_dir)
                                    for endpoint in sections_registry[section]])
                with open(sections_path / "{section}.md".format(section=section), "w", encoding="utf-8") as out:
                    out.write(result)

                result = docs.postman.create_postman_data(self, section, sections_registry[section], localization=localization)
                with open(postman_path / "{section}.postman_collection.utils.json".format(section=section), "w", encoding="utf-8") as out:
                    out.write(utils.json.minified_encoder.encode(result))

            progress.advance(main_task)
