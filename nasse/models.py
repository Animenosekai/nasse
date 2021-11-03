"""
File containing the different classes used in Nasse
"""
from abc import ABCMeta, abstractmethod
from pathlib import Path
import inspect
from inspect import getmodule
from typing import Any, Callable, Iterable, Type, Union

from nasse import exceptions
from nasse.logging import LogLevels, log
from nasse.utils.annotations import Default, is_unpackable
from nasse.utils.sanitize import sanitize_http_method, split_on_uppercase, to_path


class ABC(metaclass=ABCMeta):
    """Helper class that provides a standard way to create an ABC using
    inheritance.

    Added in the ABC module in Python 3.4
    """
    __slots__ = ()


def hello():
    """
    A dummy request handler
    """
    return "Hello world"


class Return():
    def __init__(self, name: str, example: Any = None, description: str = None, methods: Union[list[str], str] = "*", type: Any = None, children: list = None, nullable: bool = False) -> None:
        self.name = str(name)
        self.example = example
        self.description = str(description or "")
        self.type = type
        self.children = set(children or [])
        self.methods = _methods_validation(methods)
        self.all_methods = "*" in self.methods
        self.nullable = bool(nullable)

    def __repr__(self) -> str:
        return "Return({name})".format(name=self.name)

    def __copy__(self):
        return Return(
            name=self.name,
            example=self.example,
            description=self.description,
            methods=self.methods,
            type=self.type,
            children=self.children
        )


class Login():
    def __init__(self, required: bool = False, types: Union[Any, list[Any]] = [], methods: Union[list[str], str] = "*", no_login: bool = True) -> None:
        self.no_login = bool(no_login)
        self.required = bool(required)
        self.types = set()
        if types is not None:
            self.types = {t for t in types}
        self.methods = _methods_validation(methods)
        self.all_methods = "*" in self.methods

    def __repr__(self) -> str:
        if self.no_login:
            return "Login(no_login={val})".format(val=self.no_login)
        return "Login(required={required})".format(required=self.required)

    def __copy__(self):
        return Login(
            no_login=self.no_login,
            required=self.required,
            types=self.types,
            methods=self.methods
        )


class UserSent():
    def __init__(self, name: str, description: str = "", required: bool = True, methods: Union[list[str], str] = "*") -> None:
        self.name = str(name)
        self.description = str(description)
        self.required = bool(required)
        self.methods = _methods_validation(methods)
        self.all_methods = "*" in self.methods

    def __repr__(self) -> str:
        return "UserSent({name})".format(name=self.name)

    def __copy__(self):
        return UserSent(
            name=self.name,
            description=self.description,
            required=self.required,
            methods=self.methods
        )


class Header(UserSent):
    def __repr__(self) -> str:
        return "Header({name})".format(name=self.name)


class Param(UserSent):
    def __repr__(self) -> str:
        return "Param({name})".format(name=self.name)


class Cookie(UserSent):
    def __repr__(self) -> str:
        return "Cookie({name})".format(name=self.name)


class Error():
    def __init__(self, name: str, description: str = "", code: int = 500, methods: Union[list[str], str] = None) -> None:
        self.name = str(name)
        self.description = str(description)
        self.code = int(code)
        self.methods = _methods_validation(methods)
        self.all_methods = "*" in self.methods

    def __copy__(self):
        return Error(
            name=self.name,
            description=self.description,
            code=self.code,
            methods=self.methods
        )

    def __repr__(self) -> str:
        return "Error(name='{name}', code={code})".format(name=self.name, code=self.code)

# Classes Validation


def _path_to_name(path):
    """
    Internal function to turn a path into an endpoint name
    """
    return " > ".join(elem.title().replace("-", " ").replace("_", " ") for elem in str(path).split("/"))


def _methods_validation(value):
    """
    Internal function to validate a value that needs to be a list of HTTP methods
    """
    try:
        if isinstance(value, Iterable) and not isinstance(value, str):
            methods = {
                sanitize_http_method(method) for method in value}
        else:
            methods = {sanitize_http_method(value)}
        return methods
    except Exception:
        raise exceptions.NasseExceptionTBD(
            "Nasse cannot convert value of type {t} to a list of HTTP methods".format(t=value.__class__.__name__))


def _return_validation(value):
    """
    Internal function to validate a value that needs to be a `Return` instance
    """
    try:
        if isinstance(value, Return):
            return value.__copy__()
        if isinstance(value, str):
            return Return(name=value)
        if is_unpackable(value):
            try:
                return Return(**value)
            except TypeError:
                raise exceptions.NasseExceptionTBD(
                    "Either 'name' is missing or one argument doesn't have the right type while creating a Nasse.models.Return instance")
        raise ValueError  # will be catched
    except Exception as e:
        if isinstance(e, exceptions.NasseException):
            raise e
        raise exceptions.NasseExceptionTBD(
            "Nasse cannot convert value of type {t} to Nasse.models.Return".format(t=value.__class__.__name__))


def _usersent_validation(value, cast: Union[Type[UserSent], Type[Header], Type[Param], Type[Cookie]] = UserSent):
    """
    Internal function to validate a value that needs to be a `Return` instance
    """
    try:
        if isinstance(value, UserSent):
            return value.__copy__()
        if isinstance(value, str):
            return cast(name=value)
        if is_unpackable(value):
            try:
                return cast(**value)
            except TypeError:
                raise exceptions.NasseExceptionTBD(
                    "Either 'name' is missing or one argument doesn't have the right type while creating a Nasse.models.Return instance")
        raise ValueError  # will be catched
    except Exception as e:
        if isinstance(e, exceptions.NasseException):
            raise e
        raise exceptions.NasseExceptionTBD(
            "Nasse cannot convert value of type {t} to Nasse.models.{cast}".format(t=value.__class__.__name__, cast=cast.__name__))


def _error_validation(value):
    """
    Internal function to validate a value that needs to be an `Error` instance
    """
    try:
        if isinstance(value, Error):
            return value.__copy__()
        if isinstance(value, str):
            return Error(name=value)
        if isinstance(value, Exception):
            return Error(name="_".join(split_on_uppercase(value.__class__.__name__)).upper())
        if isinstance(value, type):
            return Error(name="_".join(split_on_uppercase(value.__name__)).upper())
        if is_unpackable(value):
            try:
                return Error(**value)
            except TypeError:
                raise exceptions.NasseExceptionTBD(
                    "Either 'name' is missing or one argument doesn't have the right type while creating a Nasse.models.Return instance")
        raise ValueError  # will be catched
    except Exception as e:
        if isinstance(e, exceptions.NasseException):
            raise e
        raise exceptions.NasseExceptionTBD(
            "Nasse cannot convert value of type {t} to Nasse.models.Error".format(t=value.__class__.__name__))


def _login_validation(value):
    """
    Internal function to validate a value that needs to be a `Login` instance
    """
    try:
        if isinstance(value, Login):
            return value.__copy__()
        if is_unpackable(value):
            return Login(**value)
        raise ValueError
    except Exception:
        raise exceptions.NasseExceptionTBD(
            "Nasse cannot convert value of type {t} to Nasse.models.Login".format(t=value.__class__.__name__))


class Endpoint(object):
    handler: Callable = hello
    path: str = ""
    methods: list = ["GET"]
    json: bool = True
    name: str = ""
    description: str = ""
    section: str = "Other"
    returning: list[Return] = []
    login: Login = None
    headers: list[Header] = []
    params: list[Param] = []
    cookies: list[Cookie] = []
    errors: list[Error] = []

    def __init__(self, handler: Callable = Default(hello), path: str = Default(""), methods: list[str] = Default("GET"), json: bool = Default(True), name: str = Default(""), description: str = Default(""), section: str = Default("Other"), returning: Union[Return, list[Return]] = Default([]), login: Login = Default(Login(no_login=True)), headers: Union[Header, list[Header]] = Default([]), params:  Union[Param, list[Param]] = Default([]), errors:  Union[Error, list[Error]] = Default([]), endpoint: dict = {}, **kwargs) -> None:
        results = dict(endpoint)
        results.update(kwargs)
        for key, value in [("handler", handler), ("path", path), ("methods", methods), ("json", json), ("name", name), ("description", description), ("section", section), ("returning", returning), ("login", login), ("headers", headers), ("params", params), ("errors", errors)]:
            results[key] = value if not isinstance(
                value, Default) else value.value

        for key, value in results.items():
            # performs all of the verifications
            self.__setitem__(name=key, value=value)

        if not self.path:
            try:
                self.path = to_path(inspect.getfile(self.handler).__name__) + \
                    to_path(self.handler.__name__)
            except Exception:
                module = getmodule(self.handler)
                if module.__name__ == "__main__":
                    name = Path(module.__file__).stem
                else:
                    name = module.__name__
                self.path = to_path(name) + to_path(self.handler.__name__)

        if not self.path.startswith("/"):
            self.path = "/" + self.path
        if not self.name:
            self.name = _path_to_name(self.path)
        if not self.section:
            self.section = getmodule(self.handler).__name__.title()

    def __repr__(self) -> str:
        return "Endpoint(path='{path}')".format(path=self.path)

    def keys(self) -> list:
        return {"handler", "path", "methods", "json", "name", "description", "section", "returning", "login", "headers", "cookies", "params", "errors"}

    def __getitem__(self, name):
        return getattr(self, name)

    def __setattr__(self, name: str, value: Any) -> None:
        self.__setitem__(name=name, value=value)

    def __setitem__(self, name: str, value: Any = None):
        if name == "handler":
            super().__setattr__("handler", value)
        elif name == "path":
            super().__setattr__("path", str(value))
        elif name in {"methods", "method"}:
            super().__setattr__("methods", _methods_validation(value))
        elif name == "json":
            super().__setattr__("json", bool(value))
        elif name == "name":
            super().__setattr__("name", str(value))
        elif name == "description":
            super().__setattr__("description", str(value or ""))
        elif name == "section":
            super().__setattr__("section", str(value))
        elif name == "returning":
            super().__setattr__("returning", [])
            if is_unpackable(value):
                for key, val in dict(value).items():
                    item = {"name": str(key)}
                    item.update(val)
                    self.returning.append(_return_validation(item))
            elif isinstance(value, Iterable):
                for item in value:
                    self.returning.append(_return_validation(item))
            else:
                self.returning.append(_return_validation(value))

        elif name == "login":
            super().__setattr__("login", _login_validation(value))
        elif name in {"headers", "params", "cookies", "cookie", "header", "param", "parameter", "value", "values", "args", "arg"}:
            if name in {"headers", "header"}:
                super().__setattr__("headers", [])
                storage = self.headers
                cast = Header
            elif name in {"cookie", "cookies"}:
                super().__setattr__("cookies", [])
                storage = self.cookies
                cast = Cookie
            else:
                super().__setattr__("params", [])
                storage = self.params
                cast = Param
            if is_unpackable(value):
                for key, val in dict(value).items():
                    item = {"name": str(key)}
                    item.update(val)
                    storage.append(_usersent_validation(item, cast=cast))
            elif isinstance(value, Iterable):
                for item in value:
                    storage.append(_usersent_validation(item, cast=cast))
            else:
                storage.append(_usersent_validation(value, cast))
        elif name in {"errors", "error"}:
            super().__setattr__("errors", [])
            if is_unpackable(value):
                for key, val in dict(value).items():
                    item = {"name": str(key)}
                    item.update(val)
                    self.errors.append(_error_validation(item))
            elif isinstance(value, Iterable):
                for item in value:
                    self.errors.append(_error_validation(item))
            else:
                self.errors.append(_error_validation(value))

        else:
            log("{name} is not a settable attribute for a Nasse.models.Endpoint instance".format(
                name=name), LogLevels.WARNING)

    def __delitem__(self, name):
        return delattr(self, name)

    def __contains__(self, name):
        return hasattr(self, name)

    def __copy__(self):
        """Creates a shallow copy of the current Endpoint instance (reperforms the parameters verifications)"""
        return Endpoint(
            description=self.description,
            errors=self.errors,
            headers=self.headers,
            json=self.json,
            login=self.login,
            methods=self.methods,
            name=self.name,
            params=self.params,
            path=self.path,
            returning=self.returning,
            section=self.section
        )


class AccountManagement(ABC):
    """
    An object to verify accounts used by Nasse to determine wether a request is correctly authenticated
    """
    @abstractmethod
    def retrieve_type(self, account):
        """
        An abstract method (that needs to be replaced) to retrieve the account type from a custom Account object
        """
        return None

    @abstractmethod
    def retrieve_account(self, token: str):
        """
        An abstract method (that needs to be replaced) to retrieve an Account object from a token sent by the client
        """
        return None
