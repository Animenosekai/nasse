"""
Nasse's sanitizing and convert utility
"""

import typing

import nh3
from nasse import utils

# Source: en.wikipedia.org/wiki/Whitespace_character
# Note: BRAILLE PATTERN BLANK, HANGUL FILLER, HANGUL CHOSEONG FILLER, HANGUL JUNGSEONG FILLER and
# HALFWIDTH HANGUL FILLER are also refered here as "whitespaces" while they aren't according to the Unicode standard.
WHITESPACES = ["\u0009", "\u000A", "\u000B", "\u000C", "\u000D", "\u0020", "\u0085",
               "\u00A0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004",
               "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200A", "\u2028",
               "\u2029", "\u202F", "\u205F", "\u3000", "\u180E", "\u200B", "\u200C",
               "\u200D", "\u2060", "\uFEFF", "\u00B7", "\u21A1", "\u2261", "\u237D",
               "\u23CE", "\u2409", "\u240A", "\u240B", "\u240C", "\u240D", "\u2420",
               "\u2422", "\u2423", "\u2424", "\u25B3", "\u2A5B", "\u2AAA", "\u2AAB",
               "\u3037", "\u2800", "\u3164", "\u115F", "\u1160", "\uFFA0"]
"""A list of whitespace characters"""

ALLOWED_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7',
                'h8', 'br', 'b', 'i', 'strong', 'em', 'a',
                'pre', 'code', 'img', 'tt', 'div', 'ins',
                'del', 'sup', 'sub', 'p', 'ol', 'ul', 'table',
                'thead', 'tbody', 'tfoot', 'blockquote', 'dl',
                'dt', 'dd', 'kbd', 'q', 'samp', 'var', 'hr', 'ruby',
                'rt', 'rp', 'li', 'tr', 'td', 'th', 's', 'strike',
                'summary', 'details', 'caption', 'figure',
                'figcaption', 'abbr', 'bdo', 'cite', 'dfn',
                'mark', 'small', 'span', 'time', 'wbr'}
"""Tags allowed in any HTML input"""

ALLOWED_ATTRS = {
    "*": {'abbr', 'accept', 'accept-charsetaccesskey',
          'action', 'align', 'altaria-describedby',
          'aria-hidden', 'aria-label', 'aria-labelledbyaxis',
          'border', 'cellpadding', 'cellspacing',
          'charcharoff', 'charset', 'checkedclear',
          'cols', 'colspan', 'colorcompact',
          'coords', 'datetime', 'dirdisabled',
          'enctype', 'for', 'frameheaders',
          'height', 'hreflanghspace', 'ismap',
          'label', 'langmaxlength', 'media',
          'methodmultiple', 'name', 'nohref',
          'noshadenowrap', 'open', 'progress',
          'prompt', 'readonly', 'rel', 'revrole',
          'rows', 'rowspan', 'rules', 'scopeselected',
          'shape', 'size', 'spanstart', 'summary',
          'tabindex', 'targettitle', 'type', 'usemap',
          'valign', 'valuevspace', 'width', 'itemprop'},
    "a": {'href'},
    "img": {'src', 'longdesc'},
    "div": {'itemscope', 'itemtype'},
    "blockquote": {'cite'},
    "del": {'cite'},
    "ins": {'cite'},
    "q": {'cite'}
}
"""Attributes allowed in any HTML inputs"""

ALLOWED_PROTO = {'http://*', 'https://*', 'mailto:*'}
"""Procols allowed for URLs in HTML tags"""


def remove_spaces(string: str) -> str:
    """Removes all whitespaces from the given string"""
    if not string:
        return ""
    return "".join(l for l in str(string) if l not in WHITESPACES)


def alphabetic(string: str, decimals: bool = True) -> str:
    """Removes all of the non alphabetical letters from the string"""
    if not string:
        return ""
    if decimals:
        return "".join(l for l in str(string) if l.isalpha() or l.isdecimal())
    return "".join(l for l in str(string) if l.isalpha())


def sanitize_http_method(method: str) -> str:
    """Sanitizes the given HTTP method to normalize it"""
    method = remove_spaces(method).upper()
    if method not in utils.types.HTTPMethod.ACCEPTED and method != "*":
        utils.logging.logger.warn(message="The provided HTTP method {method} does not seem "
                                  "to be in the set of defined HTTP methods".format(method=method))
    return method


def sort_http_methods(methods: typing.Iterable) -> typing.List[str]:
    """Sorts the given HTTP methods to normalize them"""
    methods = {sanitize_http_method(method) for method in methods}
    results = []
    for method in ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]:  # ordered
        if method in methods:
            results.append(method)
            methods.discard(method)
    results.extend(methods)  # remaining methods

    return results


def sanitize_text(text: str, strict: bool = True) -> str:
    """Sanitize text by removing any forbidden HTML part snippet"""
    if strict:
        # pylint: disable=no-member
        return nh3.clean(str(text), tags={"b", "i", "em", "strong"}, attributes={}, url_schemes=set())
    # pylint: disable=no-member
    return nh3.clean(str(text), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, url_schemes=ALLOWED_PROTO)


def split_on_uppercase(string: str) -> typing.List[str]:
    """
    Splits a string on any uppercase letter

    Parameters
    -----------
    string: str
        The string to split

    Returns
    -------
    list
        The string splitted
    """
    start = 0
    results = []
    string = str(string)
    length = len(string)
    for index, letter in enumerate(string):
        if letter.isupper() and (string[index - 1].islower() or (length > index + 1 and string[index + 1].islower())):
            results.append(string[start:index])
            start = index
    results.append(string[start:])
    return results

DELIMITER = "🈑"


def to_path(name: str) -> str:
    """
    Converts a method name to a path

    Parameters
    ----------
    name: str
        The name of the method/class/object
    """

    name = str(name)

    # hello__username__ --> hello/<username>
    in_variable = False
    result = ""
    name_length = len(name)
    for index, letter in enumerate(name):
        if letter == "_":
            if in_variable:  # <hello_world>
                # the previous _ got replaced by >, so we don't need to convert it too
                if result[-1] == ">":
                    result += "_"
                    continue
                # the previous _ got replaced by <, so we don't need to convert it too
                elif result[-1] == "<":
                    continue
                # "__" --> ">"
                elif index + 1 < name_length and name[index + 1] == "_":
                    in_variable = False
                    result += ">"
                else:
                    result += DELIMITER  # we want to keep any "_" inside a variable name
                    continue
            else:
                # "__" --> "<"
                if index + 1 < name_length and name[index + 1] == "_":
                    in_variable = True
                    result += "_<"
                else:  # a regular _, to be converted into "/"
                    result += letter
                    continue
        else:
            result += letter
    name = result
    # nasse.utils.sanitize --> nasse/utils/sanitize
    name = "/".join(str(name).split("."))
    # hello_world --> hello/world
    name = "/".join(name.split("_"))
    # helloWorld --> hello-world
    name = "-".join(split_on_uppercase(name)).lower()
    return "/" + name.replace(DELIMITER, "_").replace("//", "/").strip("/")

# pylint: disable=invalid-name


def toCamelCase(string: str) -> str:
    """
    Converts a string to camel case

    Parameters
    ----------
        string: str
            The string to convert
    """
    string = str(string)
    if string.isupper():
        return string
    split = string.split("_")  # split by underscore
    final_split = []
    for s in split[(1 if string.startswith("_") else 0):]:
        final_split.extend(s.split(" "))  # split by space
    return ("_" if string.startswith("_") else "") + "".join(l.capitalize() if index > 0 else l for index, l in enumerate(final_split))
