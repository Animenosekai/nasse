import base64
import io
import json
import typing

from nasse import logging, utils


class NasseJSONEncoder(json.JSONEncoder):
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

    def default(self, o: typing.Any) -> typing.Any:
        if isinstance(o, (int, float, bool, dict)):
            return o
        elif o is None:
            return None
        elif utils.annotations.is_unpackable(o):
            return dict(o)
        elif isinstance(o, bytes):
            return self.encode_bytes(o)
        elif hasattr(o, "read") and hasattr(o, "tell") and hasattr(o, "seek"):
            return self.encode_file(o)
        elif isinstance(o, typing.Iterable):
            return self.encode_iterable(o)
        else:
            logging.log("Object of type <{type}> will be converted to str while encoding to JSON".format(
                type=o.__class__.__name__))
            return str(o)


encoder = NasseJSONEncoder(ensure_ascii=False, indent=4)
minified_encoder = NasseJSONEncoder(ensure_ascii=False, separators=(",", ":"))
