"""Represents a request error"""

import typing
import dataclasses


@dataclasses.dataclass
class Error:
    """An error"""
    method: str
    url: str
    exception: Exception
    params: typing.Dict[str, list] = dataclasses.field(default_factory=dict)
    headers: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    cookies: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
