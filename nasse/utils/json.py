from base64 import b64encode
from io import BytesIO
from json import JSONEncoder
from typing import Any, Iterable

from nasse.logging import log
from nasse.utils.annotations import is_unpackable


class NasseJSONEncoder(JSONEncoder):
    def encode_bytes(self, b: bytes) -> str:
        return b64encode(b).decode("utf-8")

    def encode_file(self, f: BytesIO):
        position = f.tell()  # storing the current position
        content = f.read()  # read it (place the cursor at the end)
        f.seek(position)  # go back to the original position
        if "b" in f.mode:  # if binary mode
            return self.encode_bytes(content)
        else:
            return str(content)

    def encode_iterable(self, a: Iterable):
        return list(a)

    def default(self, o: Any) -> Any:
        if isinstance(o, (int, float, bool, dict)):
            return o
        elif o is None:
            return None
        elif is_unpackable(o):
            return dict(o)
        elif isinstance(o, bytes):
            return self.encode_bytes(o)
        elif hasattr(o, "read") and hasattr(o, "tell") and hasattr(o, "seek"):
            return self.encode_file(o)
        elif isinstance(o, Iterable):
            return self.encode_iterable(o)
        else:
            log("Object of type {type} will be converted to str while encoding to JSON".format(
                type=o.__class__.__name__))
            return str(o)


encoder = NasseJSONEncoder(ensure_ascii=False, indent=4)
minified_encoder = NasseJSONEncoder(ensure_ascii=False, separators=(",", ":"))
