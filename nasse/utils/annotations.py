import typing


class Default():
    """A default value for a function call"""

    def __init__(self, value: typing.Any = None) -> None:
        """
        A class representing the default value for any parameter in a function call

        Parameters
        -----------
            `value`: Any
                This is the default value
        """
        self.value = value

    def __repr__(self) -> str:
        return "Default({value})".format(value=self.value)


def is_unpackable(obj: typing.Any):
    """
    Checks if the given object is unpackable or not (if you can use **obj or not)
    """
    return all(hasattr(obj, attr) for attr in ('keys', '__getitem__'))
