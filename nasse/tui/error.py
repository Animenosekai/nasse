"""Represents a request error"""

import typing
import dataclasses


@dataclasses.dataclass
class Error:
    """An error"""
    exception: Exception
    method: str
    url: str
    params: typing.Dict[str, list] = dataclasses.field(default_factory=dict)
    headers: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    cookies: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    files: typing.List[typing.Tuple[str, str]] = dataclasses.field(default_factory=list)
    data: typing.Optional[bytes] = None

    timeout: float = 10
    allow_redirects: bool = True
    verify: bool = True
    proxies: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    cert: typing.List[str] = dataclasses.field(default_factory=list)
