"""
File containing the different classes used in Nasse
"""
import abc
import dataclasses
import inspect
import pathlib
import typing

from nasse import utils


# Type Aliases
T = typing.TypeVar("T")
StandardMethod = typing.Literal["GET", "HEAD", "POST",
                                "PUT", "DELETE", "CONNECT",
                                "OPTIONS", "TRACE", "PATCH"]
Method = typing.Union[StandardMethod, str]
Type = typing.Union[typing.Callable[[str], typing.Any], typing.Type]
HandlerOutput = typing.Union["response.Response", Exception, typing.Iterable, typing.Generator]


FinalMethodVariant = typing.Dict[Method, T]
FinalIterable = typing.Set[T]

MethodVariant = typing.Optional[typing.Union[FinalMethodVariant, T]]
OptionalIterable = typing.Optional[typing.Union[typing.Iterable[T], T]]


# Validations


def method_validation(method: typing.Any):
    """Validates the given method"""
    result = str(method).upper().strip()
    if result not in typing.get_args(StandardMethod) and result != "*":
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
                       value: FinalMethodVariant[FinalIterable[T]]) -> FinalIterable[T]:
    """Returns the variant defined for the given method"""
    return value.get("*", set()).union(value.get(method, set()))


def complete_cast(value: typing.Any, cast: typing.Type[T], iter: bool = False) -> T:
    """Casts the given value with the given type"""
    if iter:
        return validates_optional_iterable(value, cast)
    try:
        if isinstance(value, cast):
            return value
    except TypeError:
        pass
    if dataclasses.is_dataclass(cast):
        return cast(**value)
    return cast(value)


def validates_method_variant(value: MethodVariant[T],
                             cast: typing.Type[T],
                             iter: bool = False) -> typing.Dict[Method, T]:
    """Validates a value which might vary with the method"""
    if not value:
        return {"*": set()}
    try:
        return {method_validation(key): complete_cast(value, cast, iter)
                for key, value in {**value}.items()}
    except TypeError:
        return {"*": complete_cast(value, cast, iter)}


def validates_optional_iterable(value: OptionalIterable[T], cast: typing.Type[T]) -> typing.Set[T]:
    """Validates an iterable which might be None"""
    if not value:
        return set()
    if isinstance(value, str) or not isinstance(value, typing.Iterable):
        return {complete_cast(value, cast, iter=False)}
    return {complete_cast(val, cast, iter=False) for val in value}


# Endpoint Shaping Models


@dataclasses.dataclass
class Return:
    """A return value"""
    name: str
    """The name of the field"""
    example: typing.Any = None
    """An example of returned value"""
    description: typing.Optional[str] = None
    """A description of the returned value"""
    type: Type = str
    """The type of returned value"""
    children: typing.List["Return"] = dataclasses.field(default_factory=list)
    """The different children values"""
    nullable: bool = False
    """If this value is can be null (None)"""


def init_class(cls: typing.Type[T], instance: T, **kwargs):
    """Initialize a class"""
    if hasattr(cls, "__annotations__"):
        for attr in cls.__annotations__:
            if attr in kwargs:
                setattr(instance, attr, kwargs[attr])
            # else:
            #     setattr(instance, attr, None)


@dataclasses.dataclass
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


@dataclasses.dataclass
class UserSent:
    """A value sent by the user"""
    name: str
    description: typing.Optional[str] = None
    required: bool = True
    type: Type = str


@dataclasses.dataclass
class Dynamic(UserSent):
    """A dynamic path component"""


@dataclasses.dataclass
class Header(UserSent):
    """A header"""


@dataclasses.dataclass
class Parameter(UserSent):
    """A query parameter"""


# Backward compatibility
Param = Parameter


@dataclasses.dataclass
class Cookie(UserSent):
    """A cookie"""


@dataclasses.dataclass
class Error:
    """An error to be raised when something goes wrong"""
    name: str
    description: typing.Optional[str] = None
    code: int = 500


def non_implemented():
    """This represents a non implemented endpoint"""
    return NotImplementedError("Unitialized Endpoint")


@dataclasses.dataclass
class Endpoint:
    """Represents an endpoint"""
    handler: typing.Callable[..., HandlerOutput]
    """The function which will handle the request"""
    name: str
    """The name of the endpoint"""
    category: str
    """The category the endpoint is in"""
    sub_category: str
    """The sub category the endpoint is in"""
    description: FinalMethodVariant[str]
    """A description of what the endpoint does"""
    base_dir: pathlib.Path
    """The base directory of the endpoints,
    to define endpoints in a sub-directory without
    altering the path definition"""

    # Request
    path: str
    """The path to the endpoint"""
    methods: FinalIterable[Method]
    """The methods allowed on this endpoint"""
    login: FinalMethodVariant[FinalIterable[Login]]
    """The login rules for this endpoint.
    Defines who has access to this endpoint."""

    # User Sent
    parameters: FinalMethodVariant[FinalIterable[Parameter]]
    """The required and accepted parameters for this endpoint"""
    headers: FinalMethodVariant[FinalIterable[Header]]
    """The required and accepted headers for this endpoint"""
    cookies: FinalMethodVariant[FinalIterable[Cookie]]
    """The required and accepted cookies for this endpoint"""
    dynamics: FinalMethodVariant[FinalIterable[Dynamic]]
    """The required and accepted dynamic parts of the URL for this endpoint"""

    # Response
    json: bool
    """Whether the returned response should be JSON formatted or not"""
    returns: FinalMethodVariant[FinalIterable[Return]]
    """The structure of the returned value"""
    errors: FinalMethodVariant[FinalIterable[Error]]
    """The errors which can be raised by the endpoint"""

    @property
    def params(self):
        """An alias for `parameters`"""
        return self.parameters

    def __init__(self,
                 handler: typing.Callable[..., HandlerOutput] = non_implemented,
                 name: str = "Untitled",
                 category: str = "",
                 sub_category: str = "",
                 description: MethodVariant[str] = None,
                 base_dir: typing.Union[pathlib.Path, str, None] = None,
                 endpoint: typing.Union["Endpoint", typing.Mapping, None] = None,

                 # Request,
                 path: typing.Optional[str] = None,
                 methods: OptionalIterable[Method] = "*",
                 login: MethodVariant[OptionalIterable[Login]] = None,

                 # User Sent,
                 parameters: MethodVariant[OptionalIterable[Parameter]] = None,
                 headers: MethodVariant[OptionalIterable[Header]] = None,
                 cookies: MethodVariant[OptionalIterable[Cookie]] = None,
                 dynamics: MethodVariant[OptionalIterable[Dynamic]] = None,

                 # Response,
                 json: bool = True,
                 returns: MethodVariant[OptionalIterable[Return]] = None,
                 errors: MethodVariant[OptionalIterable[Error]] = None):

        # Merging with `endpoint`

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

        init_args = {k: v for k, v in initial.items() if v}

        try:
            extra_args = dataclasses.asdict(endpoint)
        except Exception:
            try:
                extra_args = {**endpoint}
            except Exception:
                extra_args = {}

        for key, value in extra_args.items():
            init_args.setdefault(key, value)

        for key, value in initial.items():
            init_args.setdefault(key, value)

        # init_args = {k: v for k, v in init_args.items() if v}

        # Initializing instance
        init_class(Endpoint, self, **init_args)

        # Type Validations
        self.description = validates_method_variant(self.description, str)
        self.base_dir = pathlib.Path(self.base_dir) if self.base_dir else None

        if not self.path:
            if self.base_dir:
                # Validates the base directory
                self.base_dir = pathlib.Path(self.base_dir).resolve().absolute()

                # Temp variables to manipulate the base path
                base = str(self.base_dir)
                base_len = len(base)

                # Getting the file where the function got defined
                filepath = pathlib.Path(inspect.getmodule(self.handler).__file__)

                # A fail-safe version of pathlib.Path.relative_to
                result = ""
                for index, letter in enumerate(filepath.stem):
                    # If we are still within the base path
                    # And the letter is in the base path
                    if index < base_len and letter == base[index]:
                        continue
                    result += letter
                self.path = (utils.sanitize.to_path(result)
                             + utils.sanitize.to_path(self.handler.__name__))
            else:
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

        self.parameters = validates_method_variant(self.parameters, Parameter, iter=True)
        self.headers = validates_method_variant(self.headers, Header, iter=True)
        self.cookies = validates_method_variant(self.cookies, Cookie, iter=True)
        self.dynamics = validates_method_variant(self.dynamics, Dynamic, iter=True)

        self.returns = validates_method_variant(self.returns, Return, iter=True)
        self.errors = validates_method_variant(self.errors, Error, iter=True)

        if not self.path.startswith("/"):
            self.path = "/" + self.path
        if not self.name:
            self.name = path_to_name(self.path)
        if not self.category:
            module = inspect.getmodule(self.handler)
            self.category = module.__name__.title() if module else self.category

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
