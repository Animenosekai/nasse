"""
Provides a lightweight and easy way to access CLI arguments
"""
import sys
import typing


def _enforce_iter(value: typing.Any) -> typing.List[str]:
    """Enforces the value to be a list of strings"""
    if isinstance(value, str) or not isinstance(value, typing.Iterable):
        return [str(value)]
    return [str(val) for val in value]


class Args:
    """A lightweight and easy way to access CLI arguments"""

    @classmethod
    @property
    def args(cls) -> typing.List[str]:
        """A list of CLI arguments passed in when running the program"""
        return sys.argv[1:]

    @classmethod
    def get_multiple(cls, *keys) -> typing.List[str]:
        """Gets all of the values passed in for the given keys"""
        args = _enforce_iter(cls.args)
        future = False
        results = []

        # print(keys)

        for element in args:
            if future:
                # if the previous argument was the key
                results.append(element)
                future = False
            elif element in keys:
                # if we get to the key, the next one should be the argument
                future = True
            else:
                # handling the key=value format
                name, _, value = element.partition("=")
                if name == keys:
                    results.append(value)

        return results

    @classmethod
    def get(cls, *keys, default: typing.Optional[str] = None) -> typing.Optional[str]:
        """Return the value for key if key is in the dictionary, else default"""
        results = cls.get_multiple(*keys)
        if results:
            return results[0]
        return default

    def __class_getitem__(cls, keys) -> str:
        result = cls.get(*_enforce_iter(keys))
        if not result:
            if isinstance(keys, str) or not isinstance(keys, typing.Iterable):
                keys = [str(keys)]
            args = " | ".join(f"`{key}`" for key in keys)
            raise KeyError(f"Did you forget to pass in the {args} argument ?")
        return result

    __getitem__ = __class_getitem__
    __getattr__ = __getitem__

    @classmethod
    def exists(cls, *keys) -> bool:
        """Returns if the given keys exist in the arguments"""
        if cls.get_multiple(*keys):
            return True
        return False

    def __contains__(self, keys) -> bool:
        return self.exists(*_enforce_iter(keys))
