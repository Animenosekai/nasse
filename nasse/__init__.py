"""A web server framework written on top of Flask"""

# autopep8: off
from .__info__ import * # isort:skip
from . import docs # isort:skip
from flask import g # isort:skip
from flask.wrappers import Request as FlaskRequest # isort:skip
from flask.wrappers import Response as FlaskResponse # isort:skip

from .nasse import Nasse # isort:skip
from .config import NasseConfig # isort:skip
from .request import Request # isort:skip
from .response import Response # isort:skip
from .models import * # isort:skip
from .utils.logging import Logger, LoggingLevel, logger # isort:skip


class RequestProxy(FlaskRequest, Request):
    def __init__(self) -> None:
        return

    def __getattribute__(self, name: str):
        return getattr(g.request, name)


request = RequestProxy()

# For backward compatibility
# old_name = new_name
# if something has been renamed in the new versions

# autopep8: on