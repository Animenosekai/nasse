"""
Nasse

A web server framework written on top of Flask
Stop spending time making the docs, verify the request, compress or format the response, and focus on making your next cool app!
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
__copyright__ = 'Copyright 2022, Nasse'
__credits__ = ['animenosekai']
__license__ = 'MIT License'
__version_tuple__ = (1, 1)


def __version_string__():
    if isinstance(__version_tuple__[-1], str):
        return '.'.join(map(str, __version_tuple__[:-1])) + __version_tuple__[-1]
    return '.'.join(str(i) for i in __version_tuple__)


__version__ = 'Nasse v{version}'.format(version=__version_string__())
__maintainer__ = 'Anime no Sekai'
__email__ = 'niichannomail@gmail.com'
__status__ = 'Stable'
