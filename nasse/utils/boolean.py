"""
A utility to parse boolean values
"""
import typing

from nasse import utils


def to_bool(value: typing.Any, default: bool = False):
    """
    Converts any value to a boolean

    Example
    -------
    >>> from nasse.utils.boolean import to_bool
    >>> to_bool("true")
    True
    >>> to_bool(" 1 ")
    True
    >>> to_bool(1)
    True
    >>> to_bool(" yes!")
    False
    >>> to_bool(" yes!", default=True)
    True
    >>> to_bool(" no ", default=True)
    False


    Parameters
    ----------
        value: Any
            The value to convert into a boolean
        default: bool
            The default value
    """
    if utils.sanitize.remove_spaces(value).lower() in ({"true", "1", "yes"} if not default else {"false", "0", "no"}):
        return not default
    return default
