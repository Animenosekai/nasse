"""
File containing the different classes used in Nasse
"""
import abc
import dataclasses
import inspect
import pathlib
import typing
import miko
from nasse import utils, response


class Types:
    """Holds different types"""
    # Type Aliases
    T = typing.TypeVar("T")

    class Method:
        """HTTP method types"""
        Standard = typing.Literal["GET", "HEAD", "POST",
                                  "PUT", "DELETE", "CONNECT",
                                  "OPTIONS", "TRACE", "PATCH"]
        Any = typing.Union[Standard, str]

    Type = typing.Union[str, typing.Callable[[str], typing.Any], typing.Type]
    HandlerOutput = typing.Union["response.Response", Exception, typing.Iterable, typing.Generator]

    FinalMethodVariant = typing.Dict[Method.Any, T]
    FinalIterable = typing.Set[T]

    MethodVariant = typing.Optional[typing.Union[FinalMethodVariant[T], T]]
    OptionalIterable = typing.Optional[typing.Union[typing.Iterable[T], T]]


# Validations


def method_validation(method: typing.Any):
    """Validates the given method"""
    result = str(method).upper().strip()
    if result not in typing.get_args(Types.Method.Standard) and result != "*":
        utils.logging.logger.warn(f"Defining non standard HTTP method {result}")
    return result


def path_to_name(path: str):
    """Turns a path into an endpoint name"""
    return " > ".join(elem
                      .title()
                      .replace("-", " ")
                      .replace("_", " ")
                      for elem in str(path).split("/"))


def get_method_variant(method: str,
                       value: Types.FinalMethodVariant[Types.FinalIterable[Types.T]]) -> Types.FinalIterable[Types.T]:
    """Returns the variant defined for the given method"""
    return value.get("*", set()).union(value.get(method, set()))


def complete_cast(value: typing.Any, cast: typing.Type[Types.T], iter: bool = False) -> Types.T:
    """Casts the given value with the given type"""
    if iter:
        return validates_optional_iterable(value, cast)
    try:
        if isinstance(value, cast):
            return value
    except TypeError:
        pass
    if dataclasses.is_dataclass(cast):
        if dataclasses.is_dataclass(value):
            return cast(**dataclasses.asdict(value))
        else:
            return cast(**value)
    return cast(value)


@typing.overload
def validates_method_variant(value: Types.MethodVariant[Types.T],
                             cast: typing.Type[Types.T],
                             iter: bool = True) -> typing.Dict[Types.Method.Any, Types.FinalIterable[Types.T]]: ...


@typing.overload
def validates_method_variant(value: Types.MethodVariant[Types.T],
                             cast: typing.Type[Types.T],
                             iter: bool = False) -> typing.Dict[Types.Method.Any, Types.T]: ...


def validates_method_variant(value, cast, iter=False):
    """Validates a value which might vary with the method"""
    if not value:
        if iter:
            return {"*": set()}
        else:
            return {"*": None}
    try:
        return {method_validation(key): complete_cast(value, cast, iter)
                for key, value in {**value}.items()}
    except TypeError:
        return {"*": complete_cast(value, cast, iter)}


def validates_optional_iterable(value: Types.OptionalIterable[Types.T], cast: typing.Type[Types.T]) -> typing.Set[Types.T]:
    """Validates an iterable which might be None"""
    if not value:
        return set()
    if isinstance(value, str) or not isinstance(value, typing.Iterable):
        return {complete_cast(value, cast, iter=False)}
    return {complete_cast(val, cast, iter=False) for val in value}


# Endpoint Shaping Models


@dataclasses.dataclass(eq=True, frozen=True)
class Return():
    """A return value"""
    name: str
    """The name of the field"""
    example: typing.Any = None
    """An example of returned value"""
    description: typing.Optional[str] = None
    """A description of the returned value"""
    type: Types.Type = str
    """The type of returned value"""
    children: typing.List["Return"] = dataclasses.field(default_factory=list)
    """The different children values"""
    nullable: bool = False
    """If this value is can be null (None)"""

    def __hash__(self) -> int:
        return hash(self.name) + hash(self.description) + hash(self.type) + hash(self.nullable)


def init_class(cls: typing.Type[Types.T], instance: Types.T, **kwargs):
    """Initialize a class"""
    if hasattr(cls, "__annotations__"):
        for attr in cls.__annotations__:
            if attr in kwargs:
                setattr(instance, attr, kwargs[attr])
            # else:
            #     setattr(instance, attr, None)


@dataclasses.dataclass(eq=True)
class Login:
    """Defines the rules for the login methods"""
    required: bool = False
    """If the login is required or not. The user may still authenticate."""
    types: typing.Set[typing.Any] = None
    """Accepted types of accounts"""
    skip: bool = False
    """Whether to completely skip or not the authentication step"""
    skip_fetch: bool = False
    """Whether to skip fetching the account or not.
    This effectively only checks if the provided token is correct or not."""

    def __init__(self,
                 required: bool = False,
                 types: typing.Optional[typing.Union[typing.Iterable[typing.Any],
                                                     typing.Any]] = None,
                 skip: bool = False,
                 skip_fetch: bool = False):

        init_class(Login, self,
                   required=required,
                   types=types,
                   skip=skip,
                   skip_fetch=skip_fetch)

        # Would have used __post_init__ but it doesn't support
        # having different __init__ and type annotations
        if not self.types:
            self.types = set()
        elif isinstance(self.types, str) or not isinstance(self.types, typing.Iterable):
            self.types = {self.types}
        else:
            self.types = set(self.types)

    def __hash__(self) -> int:
        result = 0
        for attr in ("required", "skip", "skip_fetch"):
            element = getattr(self, attr)
            result += hash(element)
        for element in self.types:
            result += hash(element)

        return result


@dataclasses.dataclass(eq=True, frozen=True)
class UserSent:
    """A value sent by the user"""
    name: str
    """The name of the value sent"""
    description: typing.Optional[str] = None
    """A description of the value sent"""
    required: bool = True
    """If the value is required or not"""
    type: Types.Type = str
    """The type of value sent by the user"""


Dynamic = UserSent
"""A dynamic path component"""
Header = UserSent
"""A header"""
Parameter = UserSent
"""A query parameter"""
Cookie = UserSent
"""A cookie"""

# @dataclasses.dataclass
# class Dynamic(UserSent):
#     """A dynamic path component"""


# @dataclasses.dataclass
# class Header(UserSent):
#     """A header"""


# @dataclasses.dataclass
# class Parameter(UserSent):
#     """A query parameter"""


# @dataclasses.dataclass
# class Cookie(UserSent):
#     """A cookie"""

# Backward compatibility
Param = Parameter


@dataclasses.dataclass(eq=True, frozen=True)
class Error:
    """An error to be raised when something goes wrong"""
    name: str
    """The name of the error"""
    description: typing.Optional[str] = None
    """A description of a situation where this error might be raised"""
    code: int = 500
    """The status code of the response sent along this error"""


def non_implemented():
    """This represents a non implemented endpoint"""
    return NotImplementedError("Unitialized Endpoint")


@dataclasses.dataclass
class Endpoint:
    """Represents an endpoint"""
    handler: typing.Callable[..., Types.HandlerOutput]
    """The function which will handle the request"""
    name: str
    """The name of the endpoint"""
    category: str
    """The category the endpoint is in"""
    sub_category: str
    """The sub category the endpoint is in"""
    description: Types.FinalMethodVariant[str]
    """A description of what the endpoint does"""
    base_dir: pathlib.Path
    """The base directory of the endpoints,
    to define endpoints in a sub-directory without
    altering the path definition"""

    # Request
    path: str
    """The path to the endpoint"""
    methods: Types.FinalIterable[Types.Method.Any]
    """The methods allowed on this endpoint"""
    login: Types.FinalMethodVariant[Types.FinalIterable[Login]]
    """The login rules for this endpoint.
    Defines who has access to this endpoint."""

    # User Sent
    parameters: Types.FinalMethodVariant[Types.FinalIterable[Parameter]]
    """The required and accepted parameters for this endpoint"""
    headers: Types.FinalMethodVariant[Types.FinalIterable[Header]]
    """The required and accepted headers for this endpoint"""
    cookies: Types.FinalMethodVariant[Types.FinalIterable[Cookie]]
    """The required and accepted cookies for this endpoint"""
    dynamics: Types.FinalMethodVariant[Types.FinalIterable[Dynamic]]
    """The required and accepted dynamic parts of the URL for this endpoint"""

    # Response
    json: bool
    """Whether the returned response should be JSON formatted or not"""
    returns: Types.FinalMethodVariant[Types.FinalIterable[Return]]
    """The structure of the returned value"""
    errors: Types.FinalMethodVariant[Types.FinalIterable[Error]]
    """The errors which can be raised by the endpoint"""

    @property
    def params(self):
        """An alias for `parameters`"""
        return self.parameters

    def __init__(self,
                 handler: typing.Callable[..., Types.HandlerOutput] = non_implemented,
                 name: str = "",
                 category: typing.Optional[str] = "Main",
                 sub_category: str = "",
                 description: Types.MethodVariant[str] = None,
                 base_dir: typing.Union[pathlib.Path, str, None] = None,
                 endpoint: typing.Union["Endpoint", typing.Mapping, None] = None,

                 # Request,
                 path: typing.Optional[str] = None,
                 methods: Types.OptionalIterable[Types.Method.Any] = "*",
                 login: Types.MethodVariant[Types.OptionalIterable[Login]] = None,

                 # User Sent,
                 parameters: Types.MethodVariant[Types.OptionalIterable[Parameter]] = None,
                 headers: Types.MethodVariant[Types.OptionalIterable[Header]] = None,
                 cookies: Types.MethodVariant[Types.OptionalIterable[Cookie]] = None,
                 dynamics: Types.MethodVariant[Types.OptionalIterable[Dynamic]] = None,

                 # Response,
                 json: bool = True,
                 returns: Types.MethodVariant[Types.OptionalIterable[Return]] = None,
                 errors: Types.MethodVariant[Types.OptionalIterable[Error]] = None):

        # Merging with `endpoint`
        # Could use **kwargs but it would lose the typings for type-checkers

        initial = {
            "handler": handler,
            "name": name,
            "category": category,
            "sub_category": sub_category,
            "description": description,
            "base_dir": base_dir,
            # "endpoint": endpoint,
            "path": path,
            "methods": methods,
            "login": login,
            "parameters": parameters,
            "headers": headers,
            "cookies": cookies,
            "dynamics": dynamics,
            "json": json,
            "returns": returns,
            "errors": errors
        }

        # Getting the file where the function got defined
        # module = inspect.getmodule(self.handler)
        # if module:
        #     filepath = pathlib.Path(module.__file__)
        # else:
        try:
            filepath = inspect.getsourcefile(inspect.unwrap(handler))
            if not filepath:
                raise ValueError("internal: filepath cannot be None")
        except Exception:
            filepath = handler.__code__.co_filename

        filepath = pathlib.Path(filepath or "")

        # Getting the handler signature
        signature = inspect.signature(handler)

        # Parsing the doc-string
        docs = miko.Docs(handler.__doc__ or "", signature)

        if not name:
            initial["name"] = handler.__name__

        # I might add custom parsers for each method
        if not description:
            initial["description"] = docs.description

        init_args = {k: v for k, v in initial.items() if v}

        try:
            extra_args = dataclasses.asdict(endpoint)
        except Exception:
            try:
                extra_args = {**endpoint}
            except Exception:
                extra_args = {}

        for key, value in extra_args.items():
            if key == "path":
                # `path` would seem implemented by `endpoint` but it isn't
                continue
            init_args.setdefault(key, value)

        for key, value in initial.items():
            init_args.setdefault(key, value)

        if not init_args["category"]:
            init_args["category"] = (filepath.stem or
                (handler.__module__ or "").rpartition(".")[2] or
                "Main")

        # init_args = {k: v for k, v in init_args.items() if v}

        # Initializing instance
        init_class(Endpoint, self, **init_args)

        # Type Validations
        self.description = validates_method_variant(self.description, str)
        self.base_dir = pathlib.Path(self.base_dir) if self.base_dir else pathlib.Path()

        if not self.path:
            if self.base_dir:
                # Validates the base directory
                self.base_dir = pathlib.Path(self.base_dir).resolve().absolute()

                # Temp variables to manipulate the base path
                base = self.base_dir.as_posix()
                base_len = len(base)

                # A fail-safe version of pathlib.Path.relative_to
                result = ""
                # removing the suffix
                for index, letter in enumerate(filepath.resolve().absolute().as_posix().rpartition(".")[0]):
                    # If we are still within the base path
                    # And the letter is in the base path
                    if index < base_len and letter == base[index]:
                        continue
                    result += letter
                self.path = (utils.sanitize.to_path(result)
                             + utils.sanitize.to_path(self.handler.__name__))
            else:
                # it should never come here (?)
                # it was a part used before which shouldn't be ran because we never set `base_dir` to None
                try:
                    self.path = (utils.sanitize.to_path(inspect.getfile(self.handler)) +
                                 utils.sanitize.to_path(self.handler.__name__))
                except Exception:
                    module = inspect.getmodule(self.handler)
                    if module:
                        if module.__name__ == "__main__" and module.__file__:
                            name = pathlib.Path(module.__file__).stem
                        else:
                            name = module.__name__
                    else:
                        name = ""
                    self.path = (utils.sanitize.to_path(name)
                                 + utils.sanitize.to_path(self.handler.__name__))

        self.methods = validates_optional_iterable(self.methods, method_validation)
        self.login = validates_method_variant(self.login, Login, iter=True)

        parsed_path = utils.router.Path(self.path)
        self.path = parsed_path.join(flask=True)

        self.parameters = validates_method_variant(self.parameters, Parameter, iter=True)
        self.dynamics = validates_method_variant(self.dynamics, Dynamic, iter=True)

        # retrieving all of the already defined parameters
        names = ["app", "nasse", "config", "logger", "endpoint",
                 "nasse_endpoint", "request", "method", "values",
                 "params", "parameters", "args", "form", "headers",
                 "account", "dynamics"]

        param_names = []
        for parameters in self.parameters.values():
            param_names.extend([param.name for param in parameters])

        dyn_names = []
        for dynamics in self.dynamics.values():
            dyn_names.extend([dynamic.name for dynamic in dynamics])

        names.extend(param_names)
        names.extend(dyn_names)

        names = set(names)

        # checking all of the dynamic parameters of the path
        for dynamic in parsed_path.dynamics:
            if not dynamic.name in dyn_names:
                # adding the dynamic parameter of the path to the endpoint definition
                if dynamic.name in docs.parameters.elements:
                    parameter = docs.parameters.elements[dynamic.name]

                    element = Dynamic(dynamic.name,
                                      description=parameter.body,
                                      required=not parameter.optional,
                                      type=next(iter(parameter.types)) if parameter.types else dynamic.cast)
                else:
                    element = Dynamic(dynamic.name,
                                      type=dynamic.cast)

                try:
                    self.dynamics["*"].add(element)
                except KeyError:
                    self.dynamics["*"] = {element}
                dyn_names.append(element.name)
                names.add(element.name)

        # checking the parameters defined at the function definition level
        for parameter in docs.parameters.elements.values():
            # from miko.parser.list import Parameter
            # parameter: Parameter
            if not parameter.name in names:
                # adding the parameter if it is a function argument
                element = Parameter(parameter.name,
                                    description=parameter.body,
                                    required=not parameter.optional,
                                    type=next(iter(parameter.types)) if parameter.types else None)
                try:
                    self.parameters["*"].add(element)
                except KeyError:
                    self.parameters["*"] = {element}

        self.headers = validates_method_variant(self.headers, Header, iter=True)
        self.cookies = validates_method_variant(self.cookies, Cookie, iter=True)

        try:
            handler_return = signature.return_annotation
            if not returns and issubclass(handler_return, response.Response):
                self.returns = handler_return.__returning__
        except TypeError:  # issubclass
            pass

        self.returns = validates_method_variant(self.returns, Return, iter=True)
        self.errors = validates_method_variant(self.errors, Error, iter=True)

    def __getitem__(self, key: str):
        return getattr(self, key)


class AccountManagement(abc.ABC):
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
