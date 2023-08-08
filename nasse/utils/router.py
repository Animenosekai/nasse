"""A route parser"""
import typing
from werkzeug.routing.converters import DEFAULT_CONVERTERS as FLASK_DEFAULT_CONVERTERS


class MismatchError(ValueError):
    """When the paths don't match"""


class PathNotFound(ValueError):
    """When we couldn't find the path"""


class CastError(ValueError):
    """When we couldn't cast the value to the given type"""


class Part:
    """Part of a Path"""

    def __init__(self, part: str) -> None:
        self.part = str(part)


class Dynamic(Part):
    """The dynamic part of a Path"""

    # pylint: disable=redefined-builtin
    def __init__(self, part: str, name: str, type: str = "str") -> None:
        super().__init__(part)

        self.name = str(name).strip()
        self.type = str(type).strip().lower()
        self.cast = self.caster(self.type)

        if self.type:
            self.part = f"<{self.type}:{self.name}>"
        else:
            self.part = f"<{self.name}>"

    @classmethod
    def caster(cls, type: str):
        """Returns the python class associated with the type"""
        type = str(type).lower()
        if type == "int":
            return int
        if type == "float":
            return float
        # could add more
        return str

    @property
    def flask(self) -> str:
        """Returns a flask compatible version of the part"""
        if self.type == "str":
            fixed_type = "string"
        else:
            fixed_type = self.type

        if fixed_type and fixed_type in FLASK_DEFAULT_CONVERTERS:
            return f"<{fixed_type}:{self.name}>"
        return f"<{self.name}>"


class Path:
    """A parsed Path"""

    def __init__(self, path: str) -> None:
        self.parts = self.parse(path)
        self.path = "/" + "/".join(element.part for element in self.parts)

        # Caching
        self._dynamics_num = len(self.dynamics)

    def __repr__(self) -> str:
        return f'Path("{self.path}")'

    @property
    def dynamics(self):
        """Returns the different dynamics parts of the path"""
        return [part for part in self.parts if isinstance(part, Dynamic)]

    def join(self, flask: bool = False) -> str:
        """Joins the different parts into a string"""
        if flask:
            return "/" + "/".join(element.flask if isinstance(element, Dynamic)
                                  else element.part
                                  for element in self.parts)
        return "/" + "/".join(element.part for element in self.parts)

    @classmethod
    def splitter(cls, path: str):
        """Splits the given path"""
        return str(path).strip("/").split("/")

    @classmethod
    def parse(cls, path: str) -> typing.List[Part]:
        """Returns the different parst for the given Path"""
        results = []
        for element in cls.splitter(path):
            element = str(element).strip()
            if element.startswith("<") and element.endswith(">"):
                # pylint: disable=redefined-builtin
                type, _, name = element.lstrip("<").rstrip(">").partition(":")
                if not name:
                    results.append(Dynamic(part=element, name=type))
                else:
                    results.append(Dynamic(
                        part=element,
                        name=name,
                        type=type
                    ))
            else:
                results.append(Part(part=element))
        return results

    def resolve(self, path: str):
        """Returns the different dynamic parts of the URL"""
        parts = self.splitter(path)
        if len(parts) != len(self.parts):
            raise MismatchError("The given path does not seem to be taking the right route")

        # Could use a list instead of a dictionary ?
        results = {}
        for index, part in enumerate(parts):
            element = self.parts[index]

            if isinstance(element, Dynamic):
                try:
                    results[element.name] = element.cast(part)
                except Exception as exc:
                    raise CastError(f"Couldn't cast to `{element.cast}`") from exc
                continue

            if element.part != part:
                raise MismatchError("The given path does not seem to be taking the right route")

        return results

    def is_route(self, path: str):
        """Returns if it is taking the right route"""
        try:
            self.resolve(path)
            return True
        except MismatchError:
            return False


def resolve(path: str, routes: typing.Iterable[Path]):
    """Resolves the path to determine which route to go for"""
    results: typing.List[typing.Tuple[Path, typing.Dict[str, typing.Any]]] = []

    for route in routes:
        try:
            results.append((route, route.resolve(path)))
        except MismatchError:
            continue

    if not results:
        raise PathNotFound("(404) Couldn't find the given path")

    # pylint: disable=protected-access
    return sorted(results, key=lambda element: element[0]._dynamics_num)[0]
