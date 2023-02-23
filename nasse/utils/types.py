"""
utils/types

Defining types to use on your web journey, such as enums and more
"""

import re


class LimitedString(str):
    """A string with conditions"""
    UPPER = False
    """If the string should be converted to all upper case"""
    LOWER = False
    """If the string should be converted to all lower case"""
    SPACES = True
    """If we should allow spaces in the string"""
    THROW = False
    """It we should raise an error when there is an error"""
    REGEX: re.Pattern = None
    """A Regex pattern we need to follow for this string"""
    DEFAULT = ""
    """A default value if the regex pattern is not followed"""
    LIMIT = 3000
    """A number of characters limit"""

    def __new__(self, value: str, **kw):
        value = str(value)
        if self.UPPER:
            value = value.upper()
        elif self.LOWER:
            value = value.lower()
        if not self.SPACES:
            value = value.replace(" ", "")
        if self.REGEX is not None:
            if not self.REGEX.match(value):
                if self.THROW:
                    raise ValueError("{value} is not valid".format(value))
                value = self.DEFAULT
        if len(value) > self.LIMIT:
            if self.THROW:
                raise ValueError("The given value exceeds the {limit} characters limit".format(limit=self.LIMIT))
            value = value[:self.LIMIT]
        return str.__new__(self, value, **kw)


class StringEnum(str):
    """A string enum, only accepting certain values"""
    ACCEPTED = tuple()
    DEFAULT = ""
    UPPER = True
    LOWER = False

    def __new__(self, value: str, **kw):
        value = str(value).replace(" ", "")
        if self.UPPER:
            value = value.upper()
        elif self.LOWER:
            value = value.lower()
        if value not in self.ACCEPTED:
            value = self.DEFAULT
        return str.__new__(self, value, **kw)


class Color(LimitedString):
    LIMIT = 7
    # REGEX = re.compile(r"^#[0-9a-fA-F]{6}$")
    REGEX = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")


class Email(LimitedString):
    REGEX: re.Pattern = re.compile(r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])""")
    """
    Author
    ------
    StackOverflow Community
        https://stackoverflow.com/a/201378/11557354
    """


class HTTPMethod(StringEnum):
    ACCEPTED = ("GET", "HEAD", "POST", "PUT",
                "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH")


class IPv4(LimitedString):
    REGEX = re.compile(r"""^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$""")
    """
    Author
    ------
    Danail Gabenski
        https://stackoverflow.com/a/36760050/11557354
    """


class IPv6(LimitedString):
    REGEX = re.compile(r"""(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))""")
    """
    Author
    ------
    David M. Syzdek
        https://stackoverflow.com/a/17871737/11557354
    """


class PhoneNumber(LimitedString):
    """
    Author
    ------
    Eric
        https://stackoverflow.com/a/6967885/11557354
    """
    REGEX = re.compile(
        r"""\+(9[976]\d|8[987530]\d|6[987]\d|5[90]\d|42\d|3[875]\d|2[98654321]\d|9[8543210]|8[6421]|6[6543210]|5[87654321]|4[987654310]|3[9643210]|2[70]|7|1)\d{1,14}$""")


class Filepath(LimitedString):
    REGEX = re.compile(r"""^(.+)\/([^\/]+)$""")
    """
    Author
    ------
    Paige Ruten
        https://stackoverflow.com/a/169021/11557354
    """


class URL(LimitedString):
    REGEX = re.compile(r"""[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)""")
    """
    Author
    ------
    Daveo
        https://stackoverflow.com/a/3809435/11557354
    """
