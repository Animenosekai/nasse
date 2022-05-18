"""
Nasse

© Anime no Sekai — 2021
"""
import logging
import multiprocessing
import os
import pathlib
import sys
import threading
import typing
import urllib.parse

import flask
import gunicorn
import gunicorn.app.base
import gunicorn.arbiter
import watchdog.events
import watchdog.observers

from nasse import config, docs, models, receive, request, utils
from nasse.response import exception_to_response


class FileEventHandler(watchdog.events.FileSystemEventHandler):
    def __init__(self, callback: typing.Callable, watch: typing.List[pathlib.Path], ignore: typing.List[pathlib.Path]) -> None:
        super().__init__()
        self.callback = callback
        self.watch = [str(file) for file in watch]
        self.ignore = [str(file) for file in ignore]

    def on_modified(self, event):
        src_path = str(pathlib.Path(str(event.src_path)).resolve())
        if src_path not in self.watch or src_path in self.ignore:
            return
        utils.logging.log("{path} modified".format(path=src_path))
        self.callback()


class GunicornServer(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options: dict = None):
        self.options = {
            'bind': '{host}:{port}'.format(host=config.General.HOST, port=utils.args.Args.get(("-p", "--port"), 5000)),
            'workers': 2 * multiprocessing.cpu_count() + 1,
            'capture_output': False,
            'proc_name': app.id,
            'preload_app': True,
            'worker_class': config.General.WORKER_CLASS,
            'threads': 2 * multiprocessing.cpu_count() + 1,
            'loglevel': 'error',
            # would be painful to wait 30 seconds on each reload
            'graceful_timeout': 5 if config.Mode.DEBUG else 20,
            'on_exit': self.on_exit,
            'on_starting': self.on_starting
        }
        self.options.update(options or {})
        self.application = app.flask
        formatting = {}
        if "{version}" in config.General.SERVER_HEADER:
            formatting["version"] = config.General.VERSION
        if "{app}" in config.General.SERVER_HEADER:
            formatting["app"] = app.id
        gunicorn.SERVER_SOFTWARE = config.General.SERVER_HEADER.format(
            **formatting)
        gunicorn.SERVER = config.General.SERVER_HEADER.format(**formatting)
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

    def on_starting(self, server):
        utils.logging.log("Running the server ✨",
                          level=utils.logging.LogLevels.INFO)

    def on_exit(self, server):
        utils.logging.log("Exiting... 🏮", level=utils.logging.LogLevels.INFO)


class Nasse():
    _observer = None
    _arbiter = None

    def __init__(self, name: str = None, id: str = None, account_management: models.AccountManagement = None, cors: typing.Union[str, bool, typing.Iterable] = True, max_request_size: int = 1e+9, compress: bool = True, *args, **kwargs) -> None:
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
            `cors`: str | bool | Iterable, defaults = False
                The Cross-Origin Resource Sharing (CORS) rules for the server \n
                'cors' as a string represents the allowed `Origin` \n
                'cors' as a boolean value respresents `*` when True, no CORS rules (no `Access-Control-Allow-Origin` header set) when False \n
                'cors' as an iterable represents a list of allowed `Origin`s
            `max_body_size`: int, defaults = 10^9
                The maximum size/length of the request \n
                Setting this as None is dangerous as it will not perform any content size/length check
        """
        if config.Mode.DEBUG:
            threading.settrace(
                config.General.CALL_TRACE_RECEIVER or utils.logging.add_to_call_stack)
        self.name = str(name or config.General.BASE_DIR.name or "Nasse")
        self.id = str(id or utils.sanitize.alphabetic(self.name).lower())

        if isinstance(account_management, type):
            self.account_management = account_management()
        else:
            self.account_management = account_management

        self.flask = flask.Flask(self.name, *args, **kwargs)

        if isinstance(cors, str):
            rule = utils.sanitize.remove_spaces(cors)
            if rule == "*":
                self.cors = ["*"]
            else:
                parsed = urllib.parse.urlparse(rule)
                netloc = parsed.netloc if parsed.netloc else parsed.path.split(
                    "/")[0]
                scheme = parsed.scheme or "https"
                rule = '{scheme}://{netloc}'.format(
                    scheme=scheme, netloc=netloc)
                self.cors = [rule]
        elif isinstance(cors, bool):
            self.cors = ["*"] if cors else []
        else:
            self.cors = []
            for rule in cors:
                rule = utils.sanitize.remove_spaces(rule)
                if rule == "*":
                    self.cors.append("*")
                    continue
                else:
                    parsed = urllib.parse.urlparse(rule)
                    netloc = parsed.netloc if parsed.netloc else parsed.path.split(
                        "/")[0]
                    scheme = parsed.scheme or "https"
                    rule = '{scheme}://{netloc}'.format(
                        scheme=scheme, netloc=netloc)
                    self.cors.append(rule)

        self.endpoints = {}

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

    def route(self, path: str = utils.annotations.Default(""), endpoint: models.Endpoint = None, flask_options: dict = None, **kwargs):
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
            flask_options["methods"] = new_endpoint.methods if "*" not in new_endpoint.methods else config.Enums.Conventions.HTTP_METHODS
            self.flask.add_url_rule(new_endpoint.path, flask_options.pop(
                "endpoint", None), receive.Receive(self, new_endpoint), **flask_options)
            self.endpoints[new_endpoint.path] = new_endpoint
            return new_endpoint
        return decorator

    def run(self, host: str = None, port: typing.Union[int, str] = None, watch: typing.List[str] = ["**/*.py"], ignore: typing.List[str] = [], **kwargs):
        """
        Runs the application by binding to an address and answering to clients.

        This uses Gunicorn under the hood.
        """
        parameters = {
            "bind": "{host}:{port}".format(host=host or config.General.HOST, port=port or utils.args.Args.get(("-p", "--port"), 5000))
        }
        parameters.update(kwargs)
        if config.Mode.DEBUG:
            watching = []
            ignoring = []
            for storage, data in [(watching, watch), (ignoring, ignore)]:
                for file in data:
                    file = str(file)
                    path = pathlib.Path(file)
                    if path.is_file():
                        storage.append(path.resolve())
                    elif path.is_dir():
                        storage.extend(child.resolve()
                                       for child in path.iterdir())
                    else:
                        storage.extend(child.resolve()
                                       for child in pathlib.Path().glob(file))
            utils.logging.log("DEBUG MODE IS ENABLED",
                              level=utils.logging.LogLevels.WARNING)
            self._observer = watchdog.observers.Observer()
            self._observer.schedule(FileEventHandler(
                callback=self.restart, watch=watching, ignore=ignoring), ".", recursive=True)
            self._observer.start()
        gunicorn_handler = GunicornServer(self, options=parameters)
        utils.logging.log("🎏 Binding to {color}{address}{normal}".format(
            address=gunicorn_handler.options["bind"], color=utils.logging.Colors.magenta, normal=utils.logging.Colors.normal), level=utils.logging.LogLevels.INFO)
        self._arbiter = gunicorn.arbiter.Arbiter(gunicorn_handler)
        self._arbiter.run()

        # self.flask.run(host=host, port=port, debug=debug, **kwargs)

    def restart(self):
        """Restarts the current python process"""
        utils.logging.log("Restarting... 🎐",
                          level=utils.logging.LogLevels.INFO)
        if self._observer:
            utils.logging.log("Waiting for watchdog to terminate")
            try:
                self._observer.stop()
                self._observer.join()
            except Exception:
                pass
        if self._arbiter:
            utils.logging.log("Waiting for workers to terminate")
            self._arbiter.stop()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def handle_exception(self, e):
        """
        Handles exception for flask.Flask
        """
        # from traceback import print_exc; print_exc()
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
                            response.headers["Access-Control-Allow-Methods"] = ", ".join(
                                current_endpoint.methods)
                        except Exception:
                            # from traceback import print_exc
                            # print_exc()
                            utils.logging.log(
                                "An error occured while setting the Access-Control-Allow-Methods header", utils.logging.LogLevels.WARNING)
                        try:
                            requested_headers = flask.request.headers.get(
                                "Access-Control-Request-Headers", "").split(", ")
                            endpoint_headers = [header.name.lower()
                                                for header in current_endpoint.headers]
                            if not current_endpoint.login.no_login:
                                endpoint_headers.append("authorization")
                            response.headers["Access-Control-Allow-Headers"] = ", ".join(
                                (header for header in requested_headers if header.lower() in endpoint_headers))
                        except Exception:
                            # from traceback import print_exc
                            # print_exc()
                            utils.logging.log(
                                "An error occured while setting the Access-Control-Allow-Headers header", utils.logging.LogLevels.WARNING)
                    else:
                        utils.logging.log(
                            "We couldn't verify the current endpoint informations on an OPTIONS request", utils.logging.LogLevels.WARNING)
                    if config.Mode.PRODUCTION:
                        response.headers["Access-Control-Max-Age"] = 86400
            except Exception:
                # from traceback import print_exc
                # print_exc()
                utils.logging.log(
                    "An error occured while setting some CORS headers", utils.logging.LogLevels.WARNING)

            # Allowing the right origins
            if self.cors:
                if "*" in self.cors:
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
                    if request_origin in self.cors:
                        response.headers["Access-Control-Allow-Origin"] = request_origin
                    else:
                        response.headers["Access-Control-Allow-Origin"] = self.cors[0]
            # Might need to allow the right headers
            # ...

            response.headers["Server"] = "Nasse/{version} ({name})".format(
                version=config.General.VERSION, name=self.name)

        except Exception:
            # would be bad if the `after_request` function raises an exception, especially when used as the `teardown_request`
            pass

        return response

    def make_docs(self, base_dir: typing.Union[pathlib.Path, str] = None, curl: bool = True, javascript: bool = True, python: bool = True):
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
        utils.logging.log("Creating the API Reference Documentation")

        docs_path = pathlib.Path(base_dir or pathlib.Path() / "docs")
        if not docs_path.is_dir():
            docs_path.mkdir()

        postman_path = docs_path / "postman"
        if not postman_path.is_dir():
            postman_path.mkdir()

        sections_path = docs_path / "sections"
        if not sections_path.is_dir():
            sections_path.mkdir()

        # Initializing the resulting string by prepending the header
        result = docs.header.GETTING_STARTED_HEADER.format(name=self.name, id=self.id)

        result += "## Index\n\n"

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

        headers_registry = []

        for section in sections_registry:
            current_link = docs.header.header_link(section, headers_registry)
            result += "- [{section}](./sections/{section_url}.md#{link})\n".format(section=section,
                                                                                   section_url=section.replace(" ", "%20"), link=current_link)

            result += "\n".join(["  - [{endpoint}](./sections/{section}.md#{link})".format(
                endpoint=endpoint.name,
                section=section.replace(" ", "%20"),
                link=docs.header.header_link(endpoint.name, headers_registry)) for endpoint in sections_registry[section]]
            )
            result += "\n"

        with open(docs_path / "Getting Started.md", "w", encoding="utf8") as out:
            out.write(result)

        # Dumping all of the docs and creating the Postman Data
        for section in sections_registry:
            result = docs.header.SECTION_HEADER.format(name=section)
            # result += '''\n## {section}\n'''.format(section=section)
            result += "\n".join([docs.markdown.make_docs(endpoint, curl=curl, javascript=javascript, python=python)
                                for endpoint in sections_registry[section]])
            with open(sections_path / "{section}.md".format(section=section), "w", encoding="utf-8") as out:
                out.write(result)

            result = docs.postman.create_postman_data(self, section, sections_registry[section])
            with open(postman_path / "{section}.postman_collection.utils.json".format(section=section), "w", encoding="utf-8") as out:
                out.write(utils.json.minified_encoder.encode(result))


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
