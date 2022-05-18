"""
File containing the different classes used in Nasse
"""
import abc
import inspect
import pathlib
import typing

from nasse import exceptions, logging, utils
from nasse.utils.annotations import Default


class ABC(metaclass=abc.ABCMeta):
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
    def __init__(self, name: str, example: typing.Any = None, description: str = None, methods: typing.Union[typing.List[str], str] = "*", type: typing.Any = None, children: list = None, nullable: bool = False) -> None:
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
    def __init__(self, required: bool = False, types: typing.Union[typing.Any, typing.List[typing.Any]] = [], no_login: bool = False, verification_only: bool = False) -> None:
        """
        Creates a new login model

        Parameters
        ----------
        required : bool
            Whether or not the login is required (if any error occurs while authenticating, the request will not fail)
        types : Any | list[Any]
            The types of the authorized accounts
        no_login : bool
            Will skip the authentication process
        verification_only : bool
            Will only verify the login, but not actually retrieve the account
        """
        self.no_login = bool(no_login)
        self.verification_only = bool(verification_only)
        self.required = bool(required)
        self.types = set()
        if types is not None:
            if isinstance(types, str):
                self.types = {types}
            else:
                self.types = {t for t in types}

    def __repr__(self) -> str:
        if self.no_login:
            return "Login(no_login={val})".format(val=self.no_login)
        return "Login(required={required})".format(required=self.required)

    def __copy__(self):
        return Login(
            no_login=self.no_login,
            verification_only=self.verification_only,
            required=self.required,
            types=self.types
        )


_type = type


class UserSent():
    def __init__(self, name: str, description: str = "", required: bool = True, methods: typing.Union[typing.List[str], str] = "*", type: typing.Type = None) -> None:
        self.name = str(name)
        self.description = str(description)
        self.required = bool(required)
        self.methods = _methods_validation(methods)
        self.all_methods = "*" in self.methods
        if type is None:
            self.type = None
        else:
            if not isinstance(type, _type):
                if callable(type):
                    self.type = type
                else:
                    self.type = type.__class__
            else:
                self.type = type

    def __repr__(self) -> str:
        return "UserSent({name})".format(name=self.name)

    def __copy__(self):
        return UserSent(
            name=self.name,
            description=self.description,
            required=self.required,
            methods=self.methods,
            type=self.type
        )


class Dynamic(UserSent):
    def __repr__(self) -> str:
        return "Dynamic({name})".format(name=self.name)


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
    def __init__(self, name: str, description: str = "", code: int = 500, methods: typing.Union[typing.List[str], str] = "*") -> None:
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
        if isinstance(value, typing.Iterable) and not isinstance(value, str):
            methods = {
                utils.sanitize.sanitize_http_method(method) for method in value}
        else:
            methods = {utils.sanitize.sanitize_http_method(value)}
        return methods
    except Exception:
        raise exceptions.validate.MethodsConversionError(
            "Nasse cannot convert value of type <{t}> to a list of HTTP methods".format(t=value.__class__.__name__))


def _return_validation(value):
    """
    Internal function to validate a value that needs to be a `Return` instance
    """
    try:
        if isinstance(value, Return):
            return value.__copy__()
        if isinstance(value, str):
            return Return(name=value)
        if utils.annotations.is_unpackable(value):
            try:
                return Return(**value)
            except TypeError:
                raise exceptions.validate.ReturnConversionError(
                    "Either 'name' is missing or one argument doesn't have the right type while creating a nasse.models.Return instance")
        raise ValueError  # will be catched
    except Exception as e:
        if isinstance(e, exceptions.NasseException):
            raise e
        raise exceptions.validate.ReturnConversionError(
            "Nasse cannot convert value of type <{t}> to nasse.models.Return".format(t=value.__class__.__name__))


def _usersent_validation(value, cast: typing.Union[typing.Type[UserSent], typing.Type[Header], typing.Type[Param], typing.Type[Cookie]] = UserSent):
    """
    Internal function to validate a value that needs to be a `Return` instance
    """
    try:
        if isinstance(value, UserSent):
            return value.__copy__()
        if isinstance(value, str):
            return cast(name=value)
        if utils.annotations.is_unpackable(value):
            try:
                return cast(**value)
            except TypeError:
                print(value)
                raise exceptions.validate.UserSentConversionError(
                    "Either 'name' is missing or one argument doesn't have the right type while creating a nasse.models.{cast} instance".format(cast=cast.__name__))
        raise ValueError  # will be catched
    except Exception as e:
        if isinstance(e, exceptions.NasseException):
            raise e
        raise exceptions.validate.ReturnConversionError(
            "Nasse cannot convert value of type <{t}> to Nasse.models.{cast}".format(t=value.__class__.__name__, cast=cast.__name__))


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
            return Error(name="_".join(utils.sanitize.split_on_uppercase(value.__class__.__name__)).upper())
        if isinstance(value, type):
            return Error(name="_".join(utils.sanitize.split_on_uppercase(value.__name__)).upper())
        if utils.annotations.is_unpackable(value):
            try:
                return Error(**value)
            except TypeError:
                raise exceptions.validate.ErrorConversionError(
                    "Either 'name' is missing or one argument doesn't have the right type while creating a nasse.models.Error instance")
        raise ValueError  # will be catched
    except Exception as e:
        if isinstance(e, exceptions.NasseException):
            raise e
        raise exceptions.validate.ErrorConversionError(
            "Nasse cannot convert value of type <{t}> to Nasse.models.Error".format(t=value.__class__.__name__))


def _login_validation(value):
    """
    Internal function to validate a value that needs to be a `Login` instance
    """
    try:
        if isinstance(value, Login):
            return value.__copy__()
        if utils.annotations.is_unpackable(value):
            return Login(**value)
        raise ValueError
    except Exception:
        raise exceptions.validate.LoginConversionError(
            "Nasse cannot convert value of type <{t}> to Nasse.models.Login".format(t=value.__class__.__name__))


class Endpoint(object):
    handler = hello
    path = ""
    methods = ["GET"]
    json = True
    name = ""
    description = {}
    section = "Other"
    returning = [Return("")]
    login = {"*": Login(required=False)}
    headers = [Header("")]
    params = [Param("")]
    cookies = [Cookie("")]
    dynamics = [Dynamic("")]
    errors = [Error("")]
    base_dir = None

    def __init__(self, handler: typing.Callable = Default(hello), path: str = Default(""), methods: typing.List[str] = Default("GET"), json: bool = Default(True), name: str = Default(""), description: typing.Union[str, dict[str, str]] = Default(""), section: str = Default(""), returning: typing.Union[Return, typing.List[Return]] = Default([]), login: Login = Default(Login(required=False)), headers: typing.Union[Header, typing.List[Header]] = Default([]), cookies: typing.Union[Cookie, typing.List[Cookie]] = Default([]), params: typing.Union[Param, typing.List[Param]] = Default([]), dynamics: typing.Union[Dynamic, typing.List[Dynamic]] = Default([]), errors: typing.Union[Error, typing.List[Error]] = Default([]), base_dir: str = Default(None), endpoint: dict = {}, **kwargs) -> None:
        """
        Creates a new object representing an endpoint in Nasse.

        Parameters
        ----------
        handler : typing.Callable, optional
            The function that will be called when the endpoint is called.
            Defaults to `nasse.endpoints.hello`.
        path : str, optional
            The path of the endpoint.
            By default, this is defined from the handler name using Nasse's special syntax.
        methods : typing.List[str], optional
            The HTTP methods that can be used to call the endpoint.
            Defaults to `GET`.
        json : bool, optional
            Whether the endpoint should return a JSON object.
            Defaults to `True`.
        name : str, optional
            The name of the endpoint.
        description : typing.Union[str, dict[str, str]], optional
            The description of the endpoint.
        section : str, optional
            The section/category of the endpoint.
            Defaults to `"Other"`.
        returning : typing.Union[Return, typing.List[Return]], optional
            What the endpoint returns.
        login : Login, optional
            How the user needs to be logged in to call the endpoint.
        headers : typing.Union[Header, typing.List[Header]], optional
            The headers of the endpoint.
        cookies : typing.Union[Cookie, typing.List[Cookie]], optional
            The cookies of the endpoint.
        params : typing.Union[Param, typing.List[Param]], optional
            The params of the endpoint.
        dynamics : typing.Union[Dynamic, typing.List[Dynamic]], optional
            The dynamics parts of the endpoint URL.
        errors : typing.Union[Error, typing.List[Error]], optional
            The errors which can be raised from the endpoint.
        base_dir : str, optional
            The base directory of the endpoint.
            This is useful when your files are in a subdirectory of the project.
        endpoint : dict, optional
            An endpoint object to build on top.
            Defaults to no endpoint.
        """
        results = dict(endpoint)
        # path should be different when taking 'endpoint' as the base for another endpoint
        results.pop("path", None)
        results.update(kwargs)
        for key, value in [("handler", handler), ("path", path), ("methods", methods), ("json", json), ("name", name), ("description", description), ("section", section), ("returning", returning), ("login", login), ("headers", headers), ("cookies", cookies), ("params", params), ("dynamics", dynamics), ("errors", errors), ("base_dir", base_dir)]:
            if not isinstance(value, Default):
                results[key] = value
            elif key not in results:
                results[key] = value.value
        # results.update(kwargs)

        for key, value in results.items():
            # performs all of the verifications
            self.__setitem__(name=key, value=value)

        if not self.path:
            if self.base_dir is not None:
                result = ""
                base = str(self.base_dir)
                length_of_base = len(base)
                filepath = str(pathlib.Path(
                    inspect.getmodule(self.handler).__file__).resolve())
                # removing the extension
                for index, letter in enumerate(filepath[:filepath.rfind(".")]):
                    if index < length_of_base and letter == base[index]:
                        continue
                    result += letter
                name = result
                self.path = utils.sanitize.to_path(
                    name) + utils.sanitize.to_path(self.handler.__name__)
            else:
                try:
                    self.path = utils.sanitize.to_path(inspect.getfile(self.handler).__name__) + \
                        utils.sanitize.to_path(self.handler.__name__)
                except Exception:
                    module = inspect.getmodule(self.handler)
                    if module.__name__ == "__main__":
                        name = pathlib.Path(module.__file__).stem
                    else:
                        name = module.__name__
                    self.path = utils.sanitize.to_path(
                        name) + utils.sanitize.to_path(self.handler.__name__)

        if not self.path.startswith("/"):
            self.path = "/" + self.path
        if not self.name:
            self.name = _path_to_name(self.path)
        if not self.section:
            self.section = inspect.getmodule(self.handler).__name__.title()

    def __repr__(self) -> str:
        return "Endpoint(path='{path}')".format(path=self.path)

    def keys(self) -> list:
        return {"handler", "path", "methods", "json", "name", "description", "section", "returning", "login", "headers", "cookies", "params", "dynamics", "errors", "base_dir"}

    def __getitem__(self, name):
        return getattr(self, name)

    def __setattr__(self, name: str, value: typing.Any) -> None:
        self.__setitem__(name=name, value=value)

    def __setitem__(self, name: str, value: typing.Any = None):
        if name == "handler":
            super().__setattr__("handler", value)
        elif name in {"path", "route", "rule"}:
            super().__setattr__("path", str(value))
        elif name in {"methods", "method"}:
            super().__setattr__("methods", _methods_validation(value))
        elif name == "json":
            super().__setattr__("json", bool(value))
        elif name == "name":
            super().__setattr__("name", str(value))
        elif name == "description":
            if isinstance(value, str):
                result = {"*": str(value or "")}
            else:
                result = {}
                for m, v in value.items():
                    value = str(v or "")
                    if isinstance(m, typing.Iterable):  # ["GET", "POST"]: "This is a description for the endpoint."
                        for method in _methods_validation(m):
                            result[method] = value
                    else:  # "GET": "This is a description for the endpoint."
                        result[utils.sanitize.sanitize_http_method(m)] = value
            super().__setattr__("description", result)

        elif name == "section":
            super().__setattr__("section", str(value))
        elif name in {"returning", "return", "response", "output", "answer"}:
            super().__setattr__("returning", [])
            if utils.annotations.is_unpackable(value):
                for key, val in dict(value).items():
                    item = {"name": str(key)}
                    item.update(val)
                    self.returning.append(_return_validation(item))
            elif isinstance(value, typing.Iterable):
                for item in value:
                    self.returning.append(_return_validation(item))
            else:
                self.returning.append(_return_validation(value))
        elif name == "login":
            if isinstance(value, Login):
                result = {"*": _login_validation(value)}
            else:
                try:
                    result = Login(**value)
                except TypeError:
                    result = {}
                    for m, v in value.items():
                        value = _login_validation(v)
                        if isinstance(m, typing.Iterable):
                            for method in _methods_validation(m):
                                result[method] = value
                        else:
                            result[utils.sanitize.sanitize_http_method(m)] = value
            super().__setattr__("login", result)
        elif name in {"headers", "params", "cookies", "cookie", "header", "param", "parameters", "parameter", "value", "values", "args", "arg", "dynamic", "dynamics"}:
            if name in {"headers", "header"}:
                super().__setattr__("headers", [])
                storage = self.headers
                cast = Header
            elif name in {"cookie", "cookies"}:
                super().__setattr__("cookies", [])
                storage = self.cookies
                cast = Cookie
            elif name in {"dynamic", "dynamics"}:
                super().__setattr__("dynamics", [])
                storage = self.dynamics
                cast = Dynamic
            else:
                super().__setattr__("params", [])
                storage = self.params
                cast = Param
            if utils.annotations.is_unpackable(value):
                for key, val in dict(value).items():
                    item = {"name": str(key)}
                    item.update(val)
                    storage.append(_usersent_validation(item, cast=cast))
            elif isinstance(value, typing.Iterable):
                for item in value:
                    storage.append(_usersent_validation(item, cast=cast))
            else:
                storage.append(_usersent_validation(value, cast))
        elif name in {"errors", "error"}:
            super().__setattr__("errors", [])
            if utils.annotations.is_unpackable(value):
                for key, val in dict(value).items():
                    item = {"name": str(key)}
                    item.update(val)
                    self.errors.append(_error_validation(item))
            elif isinstance(value, typing.Iterable):
                for item in value:
                    self.errors.append(_error_validation(item))
            else:
                self.errors.append(_error_validation(value))
        elif name == "base_dir":
            super().__setattr__("base_dir", pathlib.Path(
                value).resolve() if value is not None else None)
        else:
            logging.log("{name} is not a settable attribute for a Nasse.models.Endpoint instance".format(
                name=name), logging.LogLevels.WARNING)

    def __delitem__(self, name):
        return delattr(self, name)

    def __contains__(self, name):
        return hasattr(self, name)

    def __copy__(self):
        """Creates a shallow copy of the current Endpoint instance (reperforms the parameters verifications)"""
        return Endpoint(
            handler=self.handler,
            path=self.path,
            methods=self.methods,
            json=self.json,
            name=self.name,
            description=self.description,
            section=self.section,
            returning=self.returning,
            login=self.login,
            headers=self.headers,
            cookies=self.cookies,
            params=self.params,
            dynamics=self.dynamics,
            errors=self.errors,
            base_dir=self.base_dir
        )


class AccountManagement(ABC):
    """
    An object to verify accounts used by Nasse to determine wether a request is correctly authenticated
    """
    @abc.abstractmethod
    def retrieve_type(self, account):
        """
        An abstract method (that needs to be replaced) to retrieve the account type from a custom Account object
        """
        return None

    @abc.abstractmethod
    def retrieve_account(self, token: str):
        """
        An abstract method (that needs to be replaced) to retrieve an Account object from a token sent by the client
        """
        return None

    @abc.abstractmethod
    def verify_token(self, token: str):
        """
        An abstract method (that needs to be replaced) to verify a token sent by the client (to avoid retrieving the account while still checking for the token)
        """
        return None
