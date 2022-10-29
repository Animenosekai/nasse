"""
nasse/__main__

The CLI script
"""

import argparse
import contextlib
import pathlib
import importlib
import json

import nasse

from nasse.utils.types import StringEnum


class ServerEnum(StringEnum):
    ACCEPTED = ("flask", "gunicorn")
    DEFAULT = "flask"
    LOWER = True


def main():
    parser = argparse.ArgumentParser("nasse", description=nasse.__doc__)
    parser.add_argument('--version', '-v', action='version', version=nasse.__version__)
    parser.add_argument('file', action="store", type=pathlib.Path, default=pathlib.Path(), help="The file to find the Nasse instance")

    parser.add_argument("--host", action="store", type=str, required=False, default=None, help="The host to bind to")
    parser.add_argument("--port", "-p", action="store", type=int, required=False, default=None, help="The port to bind to")
    parser.add_argument("--server", "-s", action="store", type=ServerEnum, required=False, default=ServerEnum.DEFAULT,
                        help="The server to use (accepts: {accepts})".format(accepts=", ".join(ServerEnum.ACCEPTED)))
    parser.add_argument("--watch", "-w", nargs="*", default=["**/*.py"], help="Files to watch changes on debug mode")
    parser.add_argument("--ignore", "-i", nargs="*", default=[], help="Files to ignore when watching for file changes on debug mode")

    parser.add_argument("--debug", "-d", action="store_true", help="To run with debug mode enabled")
    parser.add_argument("--config", "-c", help="A configuration file for extra arguments passed to the server",
                        action="store", type=pathlib.Path, required=False, default=None)

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

    @contextlib.contextmanager
    def add_to_path(p):
        """
        Parameters
        ----------
        p: str
            the parent path
        """
        import sys
        old_path = sys.path
        sys.path = sys.path[:]
        sys.path.insert(0, p)
        try:
            yield
        finally:
            sys.path = old_path

    path = pathlib.Path(args.file).resolve().absolute()
    with add_to_path(path.parent):
        spec = importlib.util.spec_from_file_location(path.stem, str(path))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for obj in dir(module):
            element = getattr(module, obj)
            if isinstance(element, nasse.Nasse):
                element.run(
                    host=args.host,
                    port=args.port,
                    server=server,
                    watch=args.watch,
                    ignore=args.ignore,
                    **config
                )


if __name__ == "__main__":
    pass
