"""
The Nasse JSON Encoder

Most of the code here comes from the builtin `json` library
but slight changes got applied.

Copyright © 2001-2023 Python Software Foundation.

License
-------

1. This LICENSE AGREEMENT is between the Python Software Foundation
("PSF"), and the Individual or Organization ("Licensee") accessing and
otherwise using this software ("Python") in source or binary form and
its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
analyze, test, perform and/or display publicly, prepare derivative works,
distribute, and otherwise use Python alone or in any derivative version,
provided, however, that PSF's License Agreement and PSF's notice of copyright,
i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023 Python Software Foundation;
All Rights Reserved" are retained in Python alone or in any derivative version
prepared by Licensee.

3. In the event Licensee prepares a derivative work that is based on
or incorporates Python or any part thereof, and wants to make
the derivative work available to others as provided herein, then
Licensee hereby agrees to include in any such work a brief summary of
the changes made to Python.

4. PSF is making Python available to Licensee on an "AS IS"
basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
INFRINGE ANY THIRD PARTY RIGHTS.

5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.

7. Nothing in this License Agreement shall be deemed to create any
relationship of agency, partnership, or joint venture between PSF and
Licensee.  This License Agreement does not grant permission to use PSF
trademarks or trade name in a trademark sense to endorse or promote
products or services of Licensee, or any third party.

8. By copying, installing or otherwise using Python, Licensee
agrees to be bound by the terms and conditions of this License
Agreement.
"""

import base64
import io
import json
import json.encoder
import typing
import dataclasses

from nasse import utils

PYTHON_DEFAULT_DECODER = json.JSONEncoder().default


class NasseJSONEncoder(json.JSONEncoder):
    """A custom JSON encoder"""

    def _make_iterencode(self, markers, _default, _encoder, _indent, _floatstr,
                         _key_separator, _item_separator, _sort_keys, _skipkeys, _one_shot,
                         # HACK: hand-optimized bytecode; turn globals into locals
                         ValueError=ValueError,
                         dict=dict,
                         float=float,
                         id=id,
                         int=int,
                         isinstance=isinstance,
                         list=list,
                         str=str,
                         tuple=tuple,
                         _intstr=int.__repr__,
                         ):

        if _indent is not None and not isinstance(_indent, str):
            _indent = ' ' * _indent

        def _iterencode_list(lst, _current_indent_level):
            lst = self.default(lst)
            if not lst:
                yield '[]'
                return
            if markers is not None:
                markerid = id(lst)
                if markerid in markers:
                    raise ValueError("Circular reference detected")
                markers[markerid] = lst
            buf = '['
            if _indent is not None:
                _current_indent_level += 1
                newline_indent = '\n' + _indent * _current_indent_level
                separator = _item_separator + newline_indent
                buf += newline_indent
            else:
                newline_indent = None
                separator = _item_separator
            first = True
            for value in lst:
                if first:
                    first = False
                else:
                    buf = separator
                if isinstance(value, str):
                    yield buf + _encoder(value)
                elif value is None:
                    yield buf + 'null'
                elif value is True:
                    yield buf + 'true'
                elif value is False:
                    yield buf + 'false'
                elif isinstance(value, int):
                    # Subclasses of int/float may override __repr__, but we still
                    # want to encode them as integers/floats in JSON. One example
                    # within the standard library is IntEnum.
                    yield buf + _intstr(value)
                elif isinstance(value, float):
                    # see comment above for int
                    yield buf + _floatstr(value)
                else:
                    yield buf
                    if isinstance(value, (list, tuple)):
                        chunks = _iterencode_list(value, _current_indent_level)
                    elif isinstance(value, dict):
                        chunks = _iterencode_dict(value, _current_indent_level)
                    else:
                        chunks = _iterencode(value, _current_indent_level)
                    yield from chunks
            if newline_indent is not None:
                _current_indent_level -= 1
                yield '\n' + _indent * _current_indent_level
            yield ']'
            if markers is not None:
                try:
                    del markers[markerid]
                except Exception:
                    pass

        def _iterencode_dict(dct, _current_indent_level):
            dct = self.default(dct)
            if not dct:
                yield '{}'
                return
            if markers is not None:
                markerid = id(dct)
                if markerid in markers:
                    raise ValueError("Circular reference detected")
                markers[markerid] = dct
            yield '{'
            if _indent is not None:
                _current_indent_level += 1
                newline_indent = '\n' + _indent * _current_indent_level
                item_separator = _item_separator + newline_indent
                yield newline_indent
            else:
                newline_indent = None
                item_separator = _item_separator
            first = True
            if _sort_keys:
                items = sorted(dct.items())
            else:
                items = dct.items()
            for key, value in items:
                if isinstance(key, str):
                    pass
                # JavaScript is weakly typed for these, so it makes sense to
                # also allow them.  Many encoders seem to do something like this.
                elif isinstance(key, float):
                    # see comment for int/float in _make_iterencode
                    key = _floatstr(key)
                elif key is True:
                    key = 'true'
                elif key is False:
                    key = 'false'
                elif key is None:
                    key = 'null'
                elif isinstance(key, int):
                    # see comment for int/float in _make_iterencode
                    key = _intstr(key)
                elif _skipkeys:
                    continue
                else:
                    raise TypeError(f'keys must be str, int, float, bool or None, '
                                    f'not {key.__class__.__name__}')
                if first:
                    first = False
                else:
                    yield item_separator
                yield _encoder(key)
                yield _key_separator
                if isinstance(value, str):
                    yield _encoder(value)
                elif value is None:
                    yield 'null'
                elif value is True:
                    yield 'true'
                elif value is False:
                    yield 'false'
                elif isinstance(value, int):
                    # see comment for int/float in _make_iterencode
                    yield _intstr(value)
                elif isinstance(value, float):
                    # see comment for int/float in _make_iterencode
                    yield _floatstr(value)
                else:
                    if isinstance(value, (list, tuple)):
                        chunks = _iterencode_list(value, _current_indent_level)
                    elif isinstance(value, dict):
                        chunks = _iterencode_dict(value, _current_indent_level)
                    else:
                        chunks = _iterencode(value, _current_indent_level)
                    yield from chunks
            if newline_indent is not None:
                _current_indent_level -= 1
                yield '\n' + _indent * _current_indent_level
            yield '}'
            if markers is not None:
                try:
                    del markers[markerid]
                except Exception:
                    pass

        def _iterencode(o, _current_indent_level):
            o = _default(o)
            if isinstance(o, str):
                yield _encoder(o)
            elif o is None:
                yield 'null'
            elif o is True:
                yield 'true'
            elif o is False:
                yield 'false'
            elif isinstance(o, int):
                # see comment for int/float in _make_iterencode
                yield _intstr(o)
            elif isinstance(o, float):
                # see comment for int/float in _make_iterencode
                yield _floatstr(o)
            elif isinstance(o, (list, tuple)):
                yield from _iterencode_list(o, _current_indent_level)
            elif isinstance(o, dict):
                yield from _iterencode_dict(o, _current_indent_level)
            else:
                if markers is not None:
                    markerid = id(o)
                    if markerid in markers:
                        raise ValueError("Circular reference detected")
                    markers[markerid] = o
                raise TypeError('Unsupported type: {cls}'.format(cls=o.__class__.__name__))
        return _iterencode

    def encode_bytes(self, b: bytes) -> str:
        return base64.b64encode(b).decode("utf-8")

    def encode_file(self, f: io.BytesIO):
        position = f.tell()  # storing the current position
        content = f.read()  # read it (place the cursor at the end)
        f.seek(position)  # go back to the original position
        if "b" in f.mode:  # if binary mode
            return self.encode_bytes(content)
        else:
            return str(content)

    def encode_iterable(self, a: typing.Iterable):
        return list(a)

    def iterencode(self, o, _one_shot=False):
        """Encode the given object and yield each string
        representation as available.

        For example::

            for chunk in JSONEncoder().iterencode(bigobject):
                mysocket.write(chunk)

        """
        if self.check_circular:
            markers = {}
        else:
            markers = None
        if self.ensure_ascii:
            _encoder = json.encoder.py_encode_basestring_ascii
        else:
            _encoder = json.encoder.py_encode_basestring

        def floatstr(o, allow_nan=self.allow_nan,
                     _repr=float.__repr__, _inf=json.encoder.INFINITY, _neginf=-json.encoder.INFINITY):
            # Check for specials.  Note that this type of test is processor
            # and/or platform-specific, so do tests which don't depend on the
            # internals.

            if o != o:
                text = 'NaN'
            elif o == _inf:
                text = 'Infinity'
            elif o == _neginf:
                text = '-Infinity'
            else:
                return _repr(o)

            if not allow_nan:
                raise ValueError(
                    "Out of range float values are not JSON compliant: " +
                    repr(o))

            return text

        return self._make_iterencode(
            markers, self.default, _encoder, self.indent, floatstr,
            self.key_separator, self.item_separator, self.sort_keys,
            self.skipkeys, _one_shot)(o, 0)

    def default(self, o: typing.Any) -> typing.Any:
        if dataclasses.is_dataclass(o):
            o = dataclasses.asdict(o)
        if isinstance(o, str):
            return json.encoder.py_encode_basestring(o)
        elif isinstance(o, list):  # some classes inheriting from list might have implemented methods to recognize them as unpackable
            return self.encode_iterable(o)
        elif utils.unpack.is_unpackable(o):
            return dict(o)
        elif isinstance(o, bytes):
            return self.encode_bytes(o)
        elif hasattr(o, "read") and hasattr(o, "tell") and hasattr(o, "seek"):
            return self.encode_file(o)
        elif isinstance(o, typing.Iterable):
            return self.encode_iterable(o)
        try:
            return PYTHON_DEFAULT_DECODER(o)
        except TypeError:
            pass
        utils.logging.logger.debug("Object of type <{type}> will be converted to str while encoding to JSON".format(type=o.__class__.__name__))
        return str(o)


encoder = NasseJSONEncoder(ensure_ascii=False, indent=4)
minified_encoder = NasseJSONEncoder(ensure_ascii=False, separators=(",", ":"))
