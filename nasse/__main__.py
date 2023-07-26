"""
__main__

The CLI entry
"""

import argparse
import contextlib
import importlib
import json
import pathlib
import sys
import typing
import os

import nasse
from nasse.utils.types import StringEnum
from nasse.tui.apps import http_app

class ServerEnum(StringEnum):
    """The server backend to use"""
    ACCEPTED = ("flask", "gunicorn")
    DEFAULT = "flask"
    LOWER = True


def postman_to_endpoints(data: dict):
    """Turns postman data to a collection of Nasse endpoints"""
    results = []
    for element in data.get("item", []):
        req = element.get("request", {})
        url = req.get("url", {}).get("path")
        if not isinstance(url, str):
            url = "/".join(url)
        results.append(nasse.Endpoint(
            path=url,
            name=element.get("name"),
            methods=req.get("method"),
            headers=[
                nasse.Header(name=head.get("key"),
                             description=head.get("description", {}).get("content"))
                for head in req.get("header", [])
            ],
            description=req.get("description"),
            category=data.get("info", {}).get("name")
        ))
    return results


def get_nasse_instance(file: pathlib.Path):
    """Retrieves a Nasse instance from the given file"""
    file = file.resolve().absolute()
    with add_to_path(file):
        spec = importlib.util.spec_from_file_location(file.stem, str(file))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for obj in dir(module):
            element = getattr(module, obj)
            if isinstance(element, nasse.Nasse):
                # YAY
                return element
    raise ValueError("There is no `Nasse` instance in the given file")


def prepare_runnner_parser(parser: argparse.ArgumentParser):
    """Populates the parser with the `runner` app arguments"""
    # parser.add_argument("input", action="store", help="A python file containing the Nasse instance to run")

    parser.add_argument("--host", action="store", type=str, required=False, default=None, help="The host to bind to")
    parser.add_argument("--port", "-p", action="store", type=int, required=False, default=None, help="The port to bind to")
    parser.add_argument("--server", "-s", action="store", type=ServerEnum, required=False, default=ServerEnum.DEFAULT,
                        help="The server to use (accepts: {accepts})".format(accepts=", ".join(ServerEnum.ACCEPTED)))
    parser.add_argument("--watch", "-w", nargs="*", default=["**/*.py"], help="Files to watch changes on debug mode")
    parser.add_argument("--ignore", "-i", nargs="*", default=[], help="Files to ignore when watching for file changes on debug mode")

    parser.add_argument("--debug", "-d", action="store_true", help="To run with debug mode enabled")
    parser.add_argument("--config", "-c", help="A configuration file for extra arguments passed to the server",
                        action="store", type=pathlib.Path, required=False, default=None)


def get_runner_args(parser: argparse.ArgumentParser) -> typing.Dict[str, typing.Any]:
    """Retrieves the arguments to pass to Nasse"""
    args = parser.parse_args()

    if args.config:
        with open(args.config) as f:
            config = json.load(f)
    else:
        config = {}

    config["debug"] = args.debug

    if args.server == "gunicorn":
        from nasse.servers.gunicorn import Gunicorn
        server = Gunicorn
    else:
        from nasse.servers.flask import Flask
        server = Flask

    for attr in ("host", "port", "watch", "ignore"):
        config[attr] = getattr(args, attr)

    config["server"] = server
    return config


@contextlib.contextmanager
def add_to_path(path: pathlib.Path):
    """
    Parameters
    ----------
    path: pathlib.Path
        the parent path
    """
    old_path = sys.path
    sys.path = sys.path[:]
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        sys.path = old_path


def main(input: typing.Union[pathlib.Path, str]):
    """The main entrypoint"""
    instance = None
    endpoints = []

    try:
        LOAD_DIRECTORY = bool(int(os.getenv("NASSE_LOAD_DIRECTORY", "0")))
    except Exception:
        LOAD_DIRECTORY = False

    try:
        input = pathlib.Path(input)
        if input.is_file():
            try:
                data = json.loads(input.read_text())
                # Should be a list of endpoints
                # Might be a postman file or a nasse endpoints file
                endpoints.extend(postman_to_endpoints(data))
            except Exception:
                # Should be a python file
                instance = get_nasse_instance(input)

        elif input.is_dir():
            # First searching for common filenames
            for common in ("__init__.py", "app.py", "server.py", "main.py", "run.py"):
                current_input = input / common
                if current_input.is_file():
                    try:
                        instance = get_nasse_instance(current_input)
                    except Exception:
                        pass
            # Then searching through all of the files
            for element in input.iterdir():
                if element.is_file():
                    try:
                        # Might be a JSON file containing Postman data
                        data = json.loads(element.read_text())
                        endpoints.extend(postman_to_endpoints(data))
                        continue
                    except Exception:
                        pass
                    # We won't enable the directory traversing by default
                    # simply because it might load unwanted content
                    if LOAD_DIRECTORY:
                        try:
                            # Assuming this is a Python file
                            instance = get_nasse_instance(element)
                        except Exception:
                            # Welp we were wrong it might not be a file we want to load
                            pass
    except Exception:
        pass

    return instance, endpoints


def entry():
    """The entrypoint for terminals"""
    parser = argparse.ArgumentParser("nasse", description=nasse.__doc__)
    parser.add_argument("--version", "-v", action="version", version=nasse.__version__)
    parser.add_argument("input", action="store", default="", help="The file or URL to use with nasse", nargs="?")

    subparsers = parser.add_subparsers(title="app", description="The nasse app to run", required=False)
    runner_parser = subparsers.add_parser("runner", description="To run a nasse server")
    http_parser = subparsers.add_parser("http", description=http_app.__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)

    runner_parser.add_argument("file", action="store", help="A file containing the `Nasse` instance to run")
    http_parser.add_argument("link", action="store", help="The base link for the requests", nargs="?")

    prepare_runnner_parser(runner_parser)

    args, _ = parser.parse_known_args()

    instance, endpoints = main(input=args.input)

    if instance:
        prepare_runnner_parser(parser)
        return instance.run(**get_runner_args(parser))

    return http_app.HTTP(str(args.input or "http://localhost"), endpoints=endpoints).run()


if __name__ == "__main__":
    entry()
