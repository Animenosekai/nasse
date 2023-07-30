"""
XML Conversion

Source: dict2xml by delfick \n
GitHub: https://github.com/delfick/python-dict2xml \n
PyPI: https://pypi.org/project/dict2xml/ \n
Based on version 1.7.0 \n
Licensed under the MIT License

The MIT License (MIT)

Copyright (c) 2018 Stephen Moore

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

-------------------

Arranged for Nasse

It supports bytes, file-like objects, null (None), booleans, and fallback for non-supported types.
The API is also a little bit simpler.
"""
import base64
import collections
import collections.abc
import re
import typing

from nasse import utils

start_ranges = "|".join(
    "[{0}]".format(r)
    for r in [
        "\xC0-\xD6",
        "\xD8-\xF6",
        "\xF8-\u02FF",
        "\u0370-\u037D",
        "\u037F-\u1FFF",
        "\u200C-\u200D",
        "\u2070-\u218F",
        "\u2C00-\u2FEF",
        "\u3001-\uD7FF",
        "\uF900-\uFDCF",
        "\uFDF0-\uFFFD",
    ]
)

NameStartChar = re.compile(r"(:|[A-Z]|_|[a-z]|{0})".format(start_ranges))
NameChar = re.compile(r"(\-|\.|[0-9]|\xB7|[\u0300-\u036F]|[\u203F-\u2040])")

########################
# NODE
########################


class Node(object):
    """
        Represents each tag in the tree

        Each node has _either_ a single value or one or more children
        If it has a value:
            The serialized result is <%(tag)s>%(value)s</%(tag)s>

        If it has children:
            The serialized result is
                <%(wrap)s>
                    %(children)s
                </%(wrap)s>

        Which one it is depends on the implementation of self.convert
    """

    # A mapping of characters to treat as escapable entities and their replacements
    entities = [("&", "&amp;"), ("<", "&lt;"), (">", "&gt;")]

    def __init__(self, wrap="", tag="", data=None, iterables_repeat_wrap=True):
        self.tag = self.sanitize_element(tag)
        self.wrap = self.sanitize_element(wrap)
        self.data = data
        self.type = self.determine_type()
        self.iterables_repeat_wrap = iterables_repeat_wrap

        if self.type == "flat" and isinstance(self.data, str):
            # Make sure we deal with entities
            for entity, replacement in self.entities:
                self.data = self.data.replace(entity, replacement)

    def serialize(self, indenter):
        """Returns the Node serialized as an xml string"""
        # Determine the start and end of this node
        wrap = self.wrap
        end, start = "", ""
        if wrap:
            end = "</{0}>".format(wrap)
            start = "<{0}>".format(wrap)

        # Convert the data attached in this node into a value and children
        value, children = self.convert()

        # Determine the content of the node (essentially the children as a string value)
        content = ""
        if children:
            if self.type != "iterable":
                # Non-iterable wraps all it's children in the same tag
                content = indenter((c.serialize(indenter)
                                   for c in children), wrap)
            else:
                if self.iterables_repeat_wrap:
                    # Iterables repeat the wrap for each child
                    result = []
                    for c in children:
                        content = c.serialize(indenter)
                        if c.type == "flat":
                            # Child with value, it already is surrounded by the tag
                            result.append(content)
                        else:
                            # Child with children of it's own, they need to be wrapped by start and end
                            content = indenter([content], True)
                            result.append("".join((start, content, end)))

                    # We already have what we want, return the indented result
                    return indenter(result, False)
                else:
                    result = []
                    for c in children:
                        result.append(c.serialize(indenter))
                    return "".join([start, indenter(result, True), end])

        # If here, either:
        #  * Have a value
        #  * Or this node is not an iterable
        return "".join((start, value, content, end))

    def determine_type(self):
        """
            Return the type of the data on this node as an identifying string

            * Iterable : Supports "for item in data"
            * Mapping : Supports "for key in data: value = data[key]"
            * flat : A string or something that isn't iterable or a mapping
        """
        data = self.data
        if isinstance(data, (int, float, str)):
            return "flat"
        elif isinstance(data, bool):
            return "bool"
        elif data is None:
            return "null"
        elif utils.unpack.is_unpackable(data):
            return "mapping"
        elif isinstance(data, bytes):
            return "bytes"
        elif hasattr(data, "read") and hasattr(data, "tell") and hasattr(data, "seek"):
            return "file"
        elif isinstance(data, typing.Iterable):
            return "iterable"
        else:
            utils.logging.logger.debug("Object of type <{type}> will be converted to str while encoding to XML".format(type=data.__class__.__name__))
            return "flat"

    def convert(self):
        """
            Convert data on this node into a (value, children) tuple depending on the type of the data
            If the type is :
                * flat : Use self.tag to surround the value. <tag>value</tag>
                * mapping : Return a list of tags where the key for each child is the wrap for that node
                * iterable : Return a list of Nodes where self.wrap is the tag for that node
        """
        val = ""
        typ = self.type
        data = self.data
        children = []

        if typ == "mapping":
            sorted_data = data
            if not isinstance(data, collections.OrderedDict):
                sorted_data = sorted(data)

            for key in (sorted_data or []):
                item = data[key]
                children.append(
                    Node(key, "", item,
                         iterables_repeat_wrap=self.iterables_repeat_wrap)
                )

        elif typ == "iterable":
            for item in data:
                children.append(
                    Node("", self.wrap, item,
                         iterables_repeat_wrap=self.iterables_repeat_wrap,)
                )
        elif typ == "bool":
            val = "true" if data else "false"
            if self.tag:
                val = "<{0}>{1}</{2}>".format(self.tag, val, self.tag)
        elif typ == "null":
            val = "null"
            if self.tag:
                val = "<{0}>{1}</{2}>".format(self.tag, val, self.tag)
        elif typ == "bytes":
            val = base64.b64encode(data).decode("utf-8")
            if self.tag:
                val = "<{0}>{1}</{2}>".format(self.tag, val, self.tag)
        elif typ == "file":
            position = data.tell()  # storing the current position
            content = data.read()  # read it (place the cursor at the end)
            data.seek(position)  # go back to the original position
            if "b" in data.mode:  # if binary mode
                val = base64.b64encode(data).decode("utf-8")
            else:
                val = str(content)

            if self.tag:
                val = "<{0}>{1}</{2}>".format(self.tag, val, self.tag)
        else:
            val = str(data)
            if self.tag:
                val = "<{0}>{1}</{2}>".format(self.tag, val, self.tag)

        return val, children

    @staticmethod
    def sanitize_element(wrap):
        """
            Convert `wrap` into a valid tag name applying the XML Naming Rules.

                * Names can contain letters, numbers, and other characters
                * Names cannot start with a number or punctuation character
                * Names cannot start with the letters xml (or XML, or Xml, etc)
                * Names cannot contain spaces
                * Any name can be used, no words are reserved.

            :ref: http://www.w3.org/TR/REC-xml/#NT-NameChar
        """
        if wrap and isinstance(wrap, str):
            if wrap.lower().startswith("xml"):
                wrap = "_" + wrap
            return "".join(
                ["_" if not NameStartChar.match(wrap) else ""]
                + ["_" if not (NameStartChar.match(c)
                               or NameChar.match(c)) else c for c in wrap]
            )
        else:
            return wrap


def encode(data, minify: bool = False):
    """
    Encodes Python data to XML

    Parameters
    ----------
        data: Any
            The data to be converted
        minify: bool
            If the result should be minified
    """
    if minify:
        def ret(nodes, wrapped): return "".join(nodes)
    else:
        def ret(nodes, wrapped):
            """
                Indent nodes depending on value of wrapped and indent
                If not wrapped, then don't indent
                Otherwise,
                    Seperate each child by a newline
                    and indent each line in the child by one indent unit
            """
            def eachline(nodes):
                """Yield each line in each node"""
                for node in nodes:
                    for line in node.split("\n"):
                        yield line
            if wrapped:
                seperator = "\n{0}".format("    ")
                surrounding = "\n{0}{{0}}\n".format("    ")
            else:
                seperator = "\n"
                surrounding = "{0}"
            return surrounding.format(seperator.join(eachline(nodes)))

    return Node(  # wrap should be app.id
        wrap="nasse", data=data, iterables_repeat_wrap=True
    ).serialize(ret)
