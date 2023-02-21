"""
Manages GitHub flavored markdown headers
"""

import typing


def header_link(header: str, registry: typing.Optional[typing.List[str]] = None) -> str:
    """
    Generates a link from the given header

    Note: All text is converted to lowercase.
    Note: All non-word text (e.g., punctuation, HTML) is removed.
    Note: All spaces are converted to hyphens.
    Note: Two or more hyphens in a row are converted to one.
    Note: If a header with the same ID has already been generated, a unique incrementing number is appended, starting at 1.

    Parameters
    ----------
    header: str
        The header to generate the link from
    registry: list[str], optional
        An internal registry of the different created links

    Returns
    -------
    str
        A link to the header
    """
    if registry is None:
        registry = []
    # registry = registry
    result = "".join(l for l in str(header) if l.isalpha()
                     or l.isdecimal() or l == " ")
    result = result.replace(" ", "-").lower()
    final_result = ""
    for index, letter in enumerate(result):
        if letter == "-" and index > 0 and result[index - 1] != '-':
            final_result += letter
        elif index <= 0 and letter != '-':
            final_result = letter
        elif index > 0 and letter != '-':
            final_result += letter
    link_count = registry.count(final_result)
    registry.append(final_result)
    if link_count > 0:
        return "{result}-{count}".format(result=final_result, count=link_count)
    else:
        return final_result
