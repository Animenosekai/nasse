"""
Nasse\n
Catchphrase

© Anime no Sekai — 2021
"""

from . import timer
from . import logging
from . import docs
from flask import g, Request as FlaskRequest

from .nasse import Nasse
from .request import Request
from .response import Response


class RequestProxy(FlaskRequest, Request):
    def __init__(self) -> None:
        return

    def __getattribute__(self, name: str):
        return getattr(g.request, name)


request = RequestProxy()

# For backward compatibility
# old_name = new_name
# if something has been renamed in the new versions

__author__ = 'Anime no Sekai'
__copyright__ = 'Copyright 2021, Nasse'
__credits__ = ['animenosekai']
__license__ = 'MIT License'
__version__ = 'Nasse v1.0.0'
__maintainer__ = 'Anime no Sekai'
__email__ = 'niichannomail@gmail.com'
__status__ = 'Stable'
