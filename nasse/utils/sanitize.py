import bleach
from bleach import Cleaner
from bleach.linkifier import LinkifyFilter
from markdown2 import markdown
from nasse.config import Enums
from nasse.utils.logging import LogLevels, log

# Source: en.wikipedia.org/wiki/Whitespace_character
# Note: BRAILLE PATTERN BLANK, HANGUL FILLER, HANGUL CHOSEONG FILLER, HANGUL JUNGSEONG FILLER and HALFWIDTH HANGUL FILLER are also refered here as "whitespaces" while they aren't according to the Unicode standard.
WHITESPACES = ["\u0009", "\u000A", "\u000B", "\u000C", "\u000D", "\u0020", "\u0085", "\u00A0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200A", "\u2028", "\u2029", "\u202F", "\u205F", "\u3000", "\u180E", "\u200B",
               "\u200C", "\u200D", "\u2060", "\uFEFF", "\u00B7", "\u21A1", "\u2261", "\u237D", "\u23CE", "\u2409", "\u240A", "\u240B", "\u240C", "\u240D", "\u2420", "\u2422", "\u2423", "\u2424", "\u25B3", "\u2A5B", "\u2AAA", "\u2AAB", "\u3037", "\u2800", "\u3164", "\u115F", "\u1160", "\uFFA0"]
# Markdown Parsing
EXTRAS = ["code-friendly", "cuddled-lists", "fenced-code-blocks", "footnotes",
          "nofollow", "spoiler", "strike", "target-blank-links", "tables", "task_list"]
ALLOWED_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'h8', 'br', 'b', 'i', 'strong', 'em', 'a', 'pre', 'code', 'img', 'tt', 'div', 'ins', 'del', 'sup', 'sub', 'p', 'ol', 'ul', 'table', 'thead', 'tbody', 'tfoot', 'blockquote', 'dl',
                'dt', 'dd', 'kbd', 'q', 'samp', 'var', 'hr', 'ruby', 'rt', 'rp', 'li', 'tr', 'td', 'th', 's', 'strike', 'summary', 'details', 'caption', 'figure', 'figcaption', 'abbr', 'bdo', 'cite', 'dfn', 'mark', 'small', 'span', 'time', 'wbr']
ALLOWED_ATTRS = {
    "*": ['abbr', 'accept', 'accept-charsetaccesskey', 'action', 'align', 'altaria-describedby', 'aria-hidden', 'aria-label', 'aria-labelledbyaxis', 'border', 'cellpadding', 'cellspacing', 'charcharoff', 'charset', 'checkedclear', 'cols', 'colspan', 'colorcompact', 'coords', 'datetime', 'dirdisabled', 'enctype', 'for', 'frameheaders', 'height', 'hreflanghspace', 'ismap', 'label', 'langmaxlength', 'media', 'methodmultiple', 'name', 'nohref', 'noshadenowrap', 'open', 'progress', 'prompt', 'readonly', 'rel', 'revrole', 'rows', 'rowspan', 'rules', 'scopeselected', 'shape', 'size', 'spanstart', 'summary', 'tabindex', 'targettitle', 'type', 'usemap', 'valign', 'valuevspace', 'width', 'itemprop'],
    "a": ['href'],
    "img": ['src', 'longdesc'],
    "div": ['itemscope', 'itemtype'],
    "blockquote": ['cite'],
    "del": ['cite'],
    "ins": ['cite'],
    "q": ['cite']
}
ALLOWED_PROTO = ['http', 'https', 'mailto']


def remove_spaces(string: str):
    """Removes all whitespaces from the given string"""
    if string is None:
        return ""
    return "".join(l for l in str(string) if l not in WHITESPACES)


def alphabetic(string: str):
    """Removes all of the non alphabetical letters from the string"""
    if string is None:
        return ""
    return "".join(l for l in str(string) if l.isalpha())


def sanitize_http_method(method: str):
    """Sanitizes the given HTTP method to normalize it"""
    method = remove_spaces(method).upper()
    if method not in Enums.Conventions.HTTP_METHODS and method != "*":
        log(
            message="The provided HTTP method {method} does not seem to be in the set of defined HTTP methods".format(
                method=method),
            level=LogLevels.WARNING)
    return method


def markdown_to_html(md: str, table_of_content=False):
    """Markdown to HTML with Sanitizing and Link Recognition"""
    html = markdown(str(md), extras=EXTRAS +
                    (["toc"] if table_of_content else []))
    cleaner = Cleaner(tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS,
                      protocols=ALLOWED_PROTO, filters=[LinkifyFilter])
    return cleaner.clean(str(html))


def sanitize_text(text: str, strict=True):
    """Sanitize text by removing any forbidden HTML part snippet"""
    if strict:
        return bleach.clean(str(text), tags=["b", "i", "em", "strong"], attributes=[], protocols=[])
    return bleach.clean(str(text), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, protocols=ALLOWED_PROTO)


def split_on_uppercase(string: str):
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


def to_path(name: str) -> str:
    """
    Converts a method name to a path

    Parameters
    ----------
        name: str
            The name of the method/class/object
    """
    name = "/".join(str(name).split("."))
    name = "/".join(name.split("_"))
    name = "-".join(split_on_uppercase(name)).lower()
    return "/" + name.replace("//", "/").strip("/")