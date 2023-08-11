"""A web server framework written on top of Flask which lets you focus on your ideas 🍡"""

# autopep8: off
from .__info__ import __version__, __license__, __author__, __copyright__ # isort:skip
from . import docs # isort:skip
from flask import g # isort:skip
from flask.wrappers import Request as FlaskRequest # isort:skip
from flask.wrappers import Response as FlaskResponse # isort:skip

from .nasse import Nasse # isort:skip
from .config import NasseConfig # isort:skip
from .request import Request # isort:skip
from .response import Response # isort:skip
from .models import * # isort:skip
from . import logging # isort:skip
from .utils.logging import Logger, LoggingLevel, logger, log, debug # isort:skip


class RequestProxy(FlaskRequest, Request):
    """Proxies the global `Request` object"""
    def __init__(self) -> None:
        return

    def __getattribute__(self, name: str):
        return getattr(g.request, name)


request = RequestProxy()

# For backward compatibility
# old_name = new_name
# if something has been renamed in the new versions

# autopep8: on