"""
A string formatter for Nasse

Copyright
---------
Animenosekai
    MIT License
"""
import datetime
import enum
import inspect
import os
import threading
import typing
from string import Formatter

from nasse.__info__ import __version__


class Colors(enum.Enum):
    """A set of ANSI colors"""
    NORMAL = '\033[0m'
    GREY = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'


def caller_name(skip: int = 2):
    """
    Get a name of a caller in the format module.class.method

    `skip` specifies how many levels of stack to skip while getting caller
    name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

    An empty string is returned if skipped levels exceed stack height

    Note: https://stackoverflow.com/a/9812105/11557354

    Parameters
    ----------
    skip: int, default = 2
    """
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
        return ''
    parentframe = stack[start][0]
    name = []
    module = inspect.getmodule(parentframe)
    if module:
        name.append(module.__name__)
    if 'self' in parentframe.f_locals:
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append(codename)  # function or a method
    del parentframe, stack
    return ".".join(name)


class Unformatted:
    """A dummy object used by the silent formatter"""

    def __init__(self, key):
        self.key = key

    def __format__(self, format_spec):
        return "{{{}{}}}".format(self.key, ":" + format_spec if format_spec else "")


class SilentFormatter(Formatter):
    """
    A formatter which silences the KeyErrors and IndexErrors

    Author
    ------
    CodeManX
        https://stackoverflow.com/a/21754294/11557354
    """

    def get_value(self, key, args, kwargs):
        if isinstance(key, int):
            try:
                return args[key]
            except IndexError:
                return Unformatted(key)
        else:
            try:
                return kwargs[key]
            except KeyError:
                return Unformatted(key)

# pylint: disable=redefined-builtin


def format(string: str, time_format: typing.Union[str, typing.Callable[[datetime.datetime], typing.Any]] = "%Y/%m/%d, %H:%M:%S", config: "NasseConfig" = None, *args, **kwargs):
    """
    Formats the string with the given config

    Parameters
    ----------
    string: str
    time_format: typing.Union[str, typing.Callable[[datetime.datetime], typing.Any]], default = "%Y/%m/%d %H: %M:%S"
    config: NasseConfig, default = None
    level: str, default = None
    """
    formatting = {
        # colors
        "normal": Colors.NORMAL.value,
        "grey": Colors.GREY.value,
        "gray": Colors.GREY.value,
        "red": Colors.RED.value,
        "green": Colors.GREEN.value,
        "blue": Colors.BLUE.value,
        "cyan": Colors.CYAN.value,
        "turquoise": Colors.CYAN.value,
        "white": Colors.WHITE.value,
        "yellow": Colors.YELLOW.value,
        "purple": Colors.MAGENTA.value,
        "pink": Colors.MAGENTA.value,
        "magenta": Colors.MAGENTA.value
    }
    if config:
        formatting.update({
            "name": config.name,
            "app": config.name,
            "id": config.id,
            "host": config.host,
            "port": config.port,
            "debug": config.debug,
            "version": __version__,
            "base_dir": config.base_dir
        })
    time = datetime.datetime.now()
    if "{time}" in string:  # current time
        formatting["time"] = time_format(time) if callable(time_format) else time.strftime(time_format)
    if "{caller}" in string:  # caller function
        formatting["caller"] = caller_name()
    if "{thread}" in string:  # thread id
        formatting["thread"] = threading.get_ident()
    if "{pid}" in string:  # process id
        formatting["pid"] = os.getpid()
    if "{cwd}" in string:  # current working directory
        formatting["cwd"] = os.getcwd()

    # Might optionally add stuff from psutil

    return SilentFormatter().format(string, *args, **{
        **formatting,
        **kwargs
    })
