"""
Makes HTTP requests

        ╭────────────┬──────────────────────────────────────┬────────────╮
        │  History   |              Request                 |  Explorer  │
        │            | ▒▒ /path                             |            │
        │ /yay       |                                      | Reset      │
        │ POST 200   | Parameters                           | Test       │
        │            | ▒▒▒▒ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓      | ╰── Sub Cat│
        │ /no        | ▒▒▒▒ ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓      |      ╰── So│
        │ ERROR      |                                      |            │
        │            | Headers                              |            │
        │ /exist     ├──────────────────────────────────────┤            │
        │ GET 404    |               Result                 |            │
        │            | POST /yay                            |            │
        │ 4 / 8 / 62 | 200 OK in 469ms                      |            │
        │▆▆█▁▁▄▄▆▆▁▁▁|                                      |            │
        ╰────────────┴──────────────────────────────────────┴────────────╯
"""
# TODO
# - Profiles
import sys
import dataclasses
import pathlib
import time
import typing
import urllib.parse as url

import requests
from rich.traceback import Traceback
from textual import work
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.events import Click
from textual.reactive import reactive, var
from textual.suggester import Suggester
from textual.validation import Integer, Number
from textual.widgets import (Button, Footer, Header, Label,
                             LoadingIndicator, Pretty, Select, Static, Switch, Markdown,
                             Tree, _header)
from nasse.tui.components.inputs import Input
from textual.worker import get_current_worker

from nasse import __info__
from nasse.localization import EnglishLocalization, Localization, FrenchLocalization, JapaneseLocalization
from nasse.models import Endpoint, Types, UserSent, get_method_variant
from nasse.tui.app import App
from nasse.tui.components import series
from nasse.tui.components.forms import UserSentForm
from nasse.tui.components.headers import StickyHeader
from nasse.tui.components.history import HistoryResponse
from nasse.tui.components.texts import SectionTitle
from nasse.tui.screens import FileBrowser, OptionsScreen, QuitScreen
from nasse.tui.widget import Widget

# pylint: disable=pointless-string-statement
"""
╭─────────────────────────────── Dataclasses ────────────────────────────────╮
│ HTTPOptions                                                                │
│ Loading                                                                    │
│ Error                                                                      │
╰────────────────────────────────────────────────────────────────────────────╯
"""


def language_to_localization(lang: str = "eng"):
    """Returns the correct localization from the given language string"""
    if lang == JapaneseLocalization.__id__:
        return JapaneseLocalization
    elif lang == FrenchLocalization.__id__:
        return FrenchLocalization
    return EnglishLocalization

# @dataclasses.dataclass
# class Profile:
#     """A profile"""
#     name: str
#     parameters: typing.Dict[str, typing.List[str]] = dataclasses.field(default_factory=dict)
#     headers: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
#     cookies: typing.Dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class HTTPOptions:
    """App options"""
    language: str = "eng"
    timeout: float = 10
    allow_redirects: bool = True
    proxies: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    verify: bool = True
    cert: typing.List[str] = dataclasses.field(default_factory=list)
    history_limit: int = 10
    endpoints_update: int = 60
    # profiles: typing.List[Profile] = dataclasses.field(default_factory=list)
    # stream
    # hooks


@dataclasses.dataclass
class Loading:
    """The request loading state"""
    url: str


@dataclasses.dataclass
class Error:
    """An error"""
    exception: Exception
    method: str
    url: str
    params: typing.Dict[str, list] = dataclasses.field(default_factory=dict)
    headers: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    cookies: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    files: typing.List[typing.Tuple[str, str]] = dataclasses.field(default_factory=list)
    data: typing.Optional[bytes] = None

    timeout: float = 10
    allow_redirects: bool = True
    verify: bool = True
    proxies: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    cert: typing.List[str] = dataclasses.field(default_factory=list)


# pylint: disable=pointless-string-statement
"""
╭─────────────────────────────── Widgets/Views/Screens ────────────────────────────────╮
│ View                                                                                 │
│ FileInput                                                                            │
│ OptionsScreen                                                                        │
╰──────────────────────────────────────────────────────────────────────────────────────╯
"""


class View(VerticalScroll):
    """A view in the main screen"""

    def __init__(self, on_click: typing.Callable[[Click], typing.Any], **kwargs) -> None:
        super().__init__(**kwargs)
        self.when_clicked = on_click

    def on_click(self, event: Click):
        return self.when_clicked(event)


class FileInput(Widget):
    """Represents a file"""

    DEFAULT_CSS = """
    FileInput {
        width: auto;
        height: auto;
    }

    .file-input-container {
        height: auto;
    }

    .file-name {
        height: auto;
        width: 40w;
    }

    .file-input {
        height: auto;
        width: 40w;
    }

    .file-input-full {
        width: 80w;
    }

    .file-delete {
        height: auto;
        width: 10w;
    }
    """

    def __init__(self,
                 file: pathlib.Path,
                 on_delete: typing.Optional[typing.Callable[[Widget, pathlib.Path], typing.Any]] = None,
                 prompt_name: bool = True,
                 localization: typing.Type[Localization] = EnglishLocalization,
                 **kwargs):
        self.file = pathlib.Path(file)
        self.on_delete = on_delete
        self.prompt_name = prompt_name
        self.localization = localization
        super().__init__(**kwargs)

    def compose(self):
        elements = []
        if self.prompt_name:
            elements.append(Input(placeholder=self.localization.tui_name, classes="file-name"))
        file_input = Input(str(self.file.resolve()), disabled=True, classes="file-input")
        if not self.prompt_name:
            file_input.add_class("file-input-full")
        elements.append(file_input)
        elements.append(Button("Delete", "error", classes="file-delete"))
        yield Horizontal(*elements, classes="file-input-container")

    @property
    def input_name(self):
        """The file input name"""
        return self.query_one(".file-name", Input).value

    def on_button_pressed(self, event):
        """When a button is pressed"""
        if self.on_delete:
            self.on_delete(self, self.file)


class HTTPOptionsScreen(OptionsScreen[HTTPOptions]):
    """The HTTP app options screen"""

    def __init__(self,
                 base_url: str,
                 on_url_change: typing.Callable[[str], typing.Any],
                 localization: typing.Type[Localization] = EnglishLocalization,
                 **kwargs) -> None:
        self.base_url = str(base_url)
        self.on_url_change = on_url_change
        self.localization = localization
        super().__init__(**kwargs)

    def compose_options(self):
        """Composes the inner options view"""
        with VerticalScroll(id="options-inner-container"):
            yield SectionTitle(self.localization.tui_language)
            yield Select([(local.__native__, local.__id__) for local in (EnglishLocalization, FrenchLocalization, JapaneseLocalization)],
                         prompt=self.localization.tui_language,
                         allow_blank=False,
                         value=self.localization.__id__,
                         id="options-language")
            yield Label(self.localization.tui_language_notice, id="options-language-notice")

            yield SectionTitle(self.localization.tui_base_url)
            yield Input(self.base_url,
                        placeholder=self.localization.tui_base_url_placeholder,
                        id="options-base-url")

            yield SectionTitle(self.localization.tui_endpoints_update)
            yield Input(str(self.options.endpoints_update),
                        placeholder=self.localization.tui_endpoints_update_placeholder,
                        validators=[Integer(minimum=0, failure_description="The time must be a positive integer")],
                        id="options-endpoints-update")

            yield SectionTitle(self.localization.tui_history_limit)
            yield Input(str(self.options.history_limit),
                        placeholder=self.localization.tui_history_limit_placeholder,
                        validators=[Integer(minimum=0, failure_description="The limit must be a positive integer")],
                        id="options-history-limit")

            yield SectionTitle(self.localization.tui_timeout)
            yield Input(str(self.options.timeout),
                        placeholder=self.localization.tui_timeout_placeholder,
                        validators=[Number(minimum=0.0, failure_description="The timeout must be a positive number")],
                        id="options-timeout")

            yield SectionTitle(self.localization.tui_redirects)
            yield Horizontal(
                Label(self.localization.tui_allow_redirects, id="options-redirects-title", classes="options-switch-title"),
                Switch(value=self.options.allow_redirects, id="options-redirects-switch"),
                id="options-redirects-container",
                classes="options-switch-container"
            )

            yield UserSentForm(self.localization.tui_proxies, id="options-proxies", initial_values=[(UserSent(name=key), value) for key, value in self.options.proxies.items()], localization=self.localization)

            yield SectionTitle(self.localization.tui_security)
            yield Horizontal(
                Label(self.localization.tui_verify_request, id="options-verify-title", classes="options-switch-title"),
                Switch(value=self.options.verify, id="options-verify-switch"),
                id="options-verify-container",
                classes="options-switch-container"
            )

            with Container(id="certificate-files", classes="files-input-container"):
                with Container(id="certificate-files-container", classes="files-container"):
                    for file in self.options.cert:
                        yield FileInput(pathlib.Path(file), self.delete_cert_file, prompt_name=False, localization=self.localization)
                yield Button(self.localization.tui_add_certificate, id="add-certificate-button", classes="add-file-button")

    def collect_values(self) -> typing.Dict[str, typing.Any]:
        """Collect the different options value"""
        new_url = self.query_one("#options-base-url", Input).value
        if new_url != self.base_url:
            self.on_url_change(new_url)

        return {
            "language": self.query_one("#options-language", Select).value,
            "endpoints_update": int(self.query_one("#options-endpoints-update", Input).value),
            "history_limit": int(self.query_one("#options-history-limit", Input).value),
            "timeout": float(self.query_one("#options-timeout", Input).value),
            "allow_redirects": self.query_one("#options-redirects-switch", Switch).value,
            "proxies": self.query_one("#options-proxies", UserSentForm).values,
            "verify": self.query_one("#options-verify-switch", Switch).value,
            "cert": [str(inp.file) for inp in self.query(FileInput)]  # pylint: disable=not-an-iterable
        }

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """When a button is pressed"""
        event.stop()
        if event.button.has_class("add-file-button"):
            self.app.push_screen(FileBrowser(), self.add_cert_file)

    def add_cert_file(self, file: typing.Optional[pathlib.Path] = None):
        """Adds a cert file"""
        if file:
            self.query_one("#certificate-files-container", Container).mount(FileInput(file, self.delete_cert_file, prompt_name=False))

    def delete_cert_file(self, file_input: FileInput, file: pathlib.Path):
        """When a file is removed from the files list"""
        file_input.remove()


# pylint: disable=pointless-string-statement
"""
╭─────────────────────────────── App ────────────────────────────────╮
│ HTTP                                                               │
╰────────────────────────────────────────────────────────────────────╯
"""


def define_bindings(localization: typing.Type[Localization] = EnglishLocalization):
    """Defines the different bindings for the app"""
    return [("h", "toggle_history", localization.tui_history), ("r", "toggle_results", localization.tui_result), ("e", "toggle_explorer", localization.tui_explorer),
            ("s", "submit", localization.tui_submit), ("o", "open_options", localization.tui_options), ("q", "request_quit", localization.tui_quit), Binding("ctrl+c", "request_quit", localization.tui_quit, show=False)]


class HTTP(App):
    """Lets you make HTTP requests comfortably"""

    # Default values
    CSS_PATH = "../styles/http.css"
    BINDINGS = define_bindings()

    # Atrributes
    toggle_history = var(True)
    toggle_results = var(False)
    toggle_explorer = var(False)
    history: reactive[typing.List[typing.Union[requests.Response, Error]]] = reactive(list)
    result: reactive[typing.Optional[typing.Union[requests.Response, Error, Loading]]] = reactive(None)
    endpoint: reactive[typing.Optional[Endpoint]] = reactive(None)
    endpoints: reactive[typing.List[Endpoint]] = reactive(list)
    _method: reactive[Types.Method.Any] = reactive("*")
    # profile: reactive[str] = reactive("Default")

    @property
    def method(self) -> str:
        """Get the currently selected method"""
        if self._method == "*":
            try:
                return next(iter(self.endpoint.methods))
            except Exception:
                return "*"
        else:
            return self._method

    @property
    def categories(self) -> typing.Dict[str, typing.Dict[str, typing.List[Endpoint]]]:
        """Returns the category separated endpoints"""
        mid_results: typing.Dict[str, typing.List[Endpoint]] = {}
        for endpoint in self.endpoints:
            try:
                mid_results[endpoint.category].append(endpoint)
            except KeyError:
                mid_results[endpoint.category] = [endpoint]

        results = {}
        for category, endpoints in mid_results.items():
            results[category] = {}
            for endpoint in endpoints:
                try:
                    results[category][endpoint.sub_category or "@TopLevelEndpoint"].append(endpoint)
                except KeyError:
                    results[category][endpoint.sub_category or "@TopLevelEndpoint"] = [endpoint]
        return results

    def __init__(self,
                 link: str,  # The base link
                 endpoints: typing.Optional[typing.List[Endpoint]] = None,  # Endpoints for the endpoints explorer
                 #  localization: typing.Union[Localization, typing.Type[Localization]] = EnglishLocalization,  # The UI language
                 options: typing.Optional[HTTPOptions] = None,  # Options for the app
                 **kwargs):
        super().__init__(**kwargs)
        self.link = url.urlparse(link)

        # self.localization = localization
        self.endpoints = endpoints or []
        self.base_endpoints = self.endpoints.copy()

        self.options = options or HTTPOptionsScreen.loads("http", HTTPOptions)
        self.localization = language_to_localization(self.options.language)

        self.set_bindings(define_bindings(self.localization))

    @work(exclusive=True)
    def update_endpoints(self, wait: int = 0):
        """The worker thread which updates the endpoints list"""
        worker = get_current_worker()
        time.sleep(wait)
        while True:
            # print("(worker) Checking out the new endpoints")
            try:
                final_path = url.urlunparse((
                    # Defaulting to the registered base URL
                    self.link.scheme,
                    self.link.netloc,
                    "/@nasse/endpoints",
                    "",
                    "",
                    ""
                ))
                response = requests.get(final_path, timeout=60)
                endpoints = []
                for endpoint in response.json()["data"]["endpoints"]:
                    # print(endpoint)
                    endpoint.pop("handler", None)
                    endpoints.append(Endpoint(**endpoint))

            except Exception as err:
                # print("(worker) Opps an error occured while checking for new endpoints", err)
                endpoints = []

            if not worker.is_cancelled:
                self.call_from_thread(self.load_endpoints, endpoints)

            # print(f"(worker) Waiting {self.options.endpoints_update} seconds before checking again for new endpoints")

            # This is a big approximate way of doing this but it's fine because
            # this is not very important
            for _ in range(self.options.endpoints_update):
                if worker.is_cancelled:
                    break
                time.sleep(1)

            if worker.is_cancelled:
                # print("(worker) The endpoints checking got cancelled here")
                break

    def load_endpoints(self, endpoints: typing.List[Endpoint]):
        """Loads the endpoints to the endpoints list"""
        self.endpoints = [*self.base_endpoints, *endpoints]
        # print(f"Found {len(self.endpoints)} endpoints")

    # pylint: disable=pointless-string-statement
    """
    ╭─────────────────────────────── Composers ────────────────────────────────╮
    │ compose                                                                  │
    │ compose_request_view                                                     │
    │ compose_result_start                                                     │
    │ compose_result_error                                                     │
    │ compose_result_loading                                                   │
    │ compose_result_response                                                  │
    │ compose_explorer                                                         │
    ╰──────────────────────────────────────────────────────────────────────────╯
    """

    def compose(self):
        """
        Draws the screen

        Area
        ----
        ╭────────────────────────────────────────────────╮
        │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
        │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
        │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
        │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
        │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
        │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
        │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
        │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
        │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
        ╰────────────────────────────────────────────────╯
        """
        # The header icon will be changed inside the `on_mount` event of this class
        yield Header(show_clock=True)

        # Coverage: Screen
        with Horizontal(id="screen"):
            with Container(id="history"):
                # History
                # Coverage: Left sidebar
                yield StickyHeader(self.localization.tui_history)
                with VerticalScroll(id="history-requests"):
                    # Requests History
                    # This displays a list of already made
                    # requests, whether it be successful or
                    # erroneous ones, in chronological orders.
                    for response in self.history:
                        yield HistoryResponse(response)
                # This displays a graph with the evolution of the time
                # taken for each request
                yield series.TimeSeries([], localization=self.localization, id="history-ping")

            with Container(id="main"):
                # Main Page
                # Coverage: Center of the screen
                yield StickyHeader(self.localization.tui_request, id="request-title")

                # There are actually two views, one for the actual request customisation
                # and one for the request response.
                # They both can be expanded as the user needs by focusing on them.

                # The request customisation
                with View(id="request", on_click=self.on_request_view_clicked):
                    # The actual content is explained below in `compose_request_view`
                    yield from self.compose_request_view()

                # The request response
                with View(id="result", on_click=self.on_result_view_clicked):
                    # Request Result
                    yield StickyHeader(self.localization.tui_result)
                    # This content will be changed by the `compose_result_*` functions
                    # Refer to those functions for further details.
                    yield from self.compose_result_start()

            with Container(id="explorer"):
                # Endpoints explorer
                # Coverage: Right sidebar

                # The endpoints explorer is a feature which lets the user
                # use existing endpoints information to guide them through
                # their use.
                # It prefills the sendable values names, adds a description
                # for items which supports them and allows for a greater
                # understanding of the whole server pathspace.
                yield StickyHeader(self.localization.tui_explorer)

                # This overwrites all of the changes made
                yield Button(self.localization.tui_reset, id="explorer-reset")

                # The actual explorer
                # with VerticalScroll(id="endpoints-explorer"):
                with VerticalScroll(id="tree-view"):
                    yield from self.compose_explorer()

        # Add a footer, which automatically displays the different available bindings
        yield Footer()

    def compose_request_view(self):
        """
        Creates the request customisation view

        Area
        ----
        ╭────────┬──────────────────────────────┬────────╮
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        │        ├──────────────────────────────┤        │
        │        |                              |        │
        │        |                              |        │
        ╰────────┴──────────────────────────────┴────────╯

        Note: Comments marked with a `(*)` have method variants, which shows that they might change with the method selected by the user.
        """

        # Caching the selected method
        method = self.method

        if self.endpoint:
            # We can actually display the name and description for defined endpoints
            description = self.endpoint.description.get(method, self.endpoint.description.get("*", self.localization.no_description))
            # We are forced to use this syntax since the context manager doesn't seem to work well
            # with the `mount` and `mount_all` functions
            yield Container(
                Label(self.endpoint.name, id="request-information-title"),  # A box with the endpoint name
                Markdown(description.strip(), id="request-information-description"),  # A blockquote with the endpoint description (*)
                id="request-information"
            )

        if not self.endpoint or not self.endpoint.methods or "*" in self.endpoint.methods:
            # All of the methods might be available
            methods = typing.get_args(Types.Method.Standard)
        else:
            # The endpoint only supports these methods
            methods = self.endpoint.methods

        yield Horizontal(Select([(method, method) for method in methods],
                                allow_blank=False,
                                value=method if method != "*" else "GET",
                                id="request-method"),
                         Input(self.endpoint.path if self.endpoint else "/",
                               placeholder=self.localization.tui_path,
                               suggester=PathSuggestion(self),
                               id="request-path"),
                         id="request-path-container")

        yield Container(UserSentForm(self.localization.parameters, inputs=get_method_variant(method, self.endpoint.parameters)
                                     if self.endpoint else None, multiple=True, id="request-parameters", localization=self.localization),
                        UserSentForm(self.localization.headers, inputs=get_method_variant(method, self.endpoint.headers)
                                     if self.endpoint else None, id="request-headers", localization=self.localization),
                        UserSentForm(self.localization.cookies, inputs=get_method_variant(method, self.endpoint.cookies)
                                     if self.endpoint else None, id="request-cookies", localization=self.localization),
                        id="request-user-sent")

        yield SectionTitle(self.localization.tui_file)
        yield Container(Container(id="request-files-container", classes="files-container"),
                        Button(self.localization.tui_add_file, classes="add-file-button"),
                        classes="files-input-container")

        yield SectionTitle(self.localization.tui_data)
        yield Container(Button(self.localization.tui_add_data_file, id="request-data-button"), id="request-data-container")

    def compose_result_response(self, result: requests.Response):
        """
        Creates the response view for a successful request

        Area
        ----
        ╭────────┬──────────────────────────────┬────────╮
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        ├──────────────────────────────┤        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        ╰────────┴──────────────────────────────┴────────╯
        """
        yield Label(f"{result.request.method} {result.url}", id="result-title")
        yield Label(f"[bold]{result.status_code}[/bold] {result.reason} [grey]in {series.transform_time(result.elapsed.total_seconds() * 1000)}[/grey]", id="result-subtitle")

        if result.headers:
            yield SectionTitle(self.localization.headers)
            yield Label('\n'.join(f'{name}: {file}' for name, file in result.headers.items()))

        if result.cookies:
            yield SectionTitle(self.localization.cookies)
            yield Label('\n'.join(f'{name}: {file}' for name, file in result.cookies.items()))

        content = None
        try:
            content = result.json()
        except Exception:
            pass

        if not content:
            try:
                content = result.text
            except Exception:
                pass

        if not content:
            try:
                content = result.content
            except Exception:
                content = f"[red](ERROR)[/red] {self.localization.tui_no_content}"

        yield SectionTitle(self.localization.tui_content)
        yield Label(f"({sys.getsizeof(content)} bytes)", id="result-size")
        yield Pretty(content, id="result-content")

    def compose_result_start(self):
        """
        Creates the response view when no request is selected.

        Area
        ----
        ╭────────┬──────────────────────────────┬────────╮
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        ├──────────────────────────────┤        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        ╰────────┴──────────────────────────────┴────────╯
        """
        # Prompts the user to make a request, because it is highly likely that no request has been made
        yield Label(self.localization.tui_start_prompt, id="empty-result-label")

    def compose_result_loading(self, result: Loading):
        """
        Creates the response view when a request is being made

        Area
        ----
        ╭────────┬──────────────────────────────┬────────╮
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        ├──────────────────────────────┤        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        ╰────────┴──────────────────────────────┴────────╯
        """
        yield Container(
            Horizontal(
                Label("🧑‍💻"),  # the user
                LoadingIndicator(),  # is making a request
                Label("🌐"),  # to the server
                id="loading-container"
            ),
            Label(self.localization.tui_contacting.format(url=url.urlparse(result.url).netloc)),  # the server hostname
            id="loading-view"
        )

    def compose_result_error(self, result: Error):
        """
        Creates the response view for an error

        Area
        ----
        ╭────────┬──────────────────────────────┬────────╮
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        |                              |        │
        │        ├──────────────────────────────┤        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        │        |▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒|        │
        ╰────────┴──────────────────────────────┴────────╯
        """
        yield Label(f"{result.method} {result.url}", id="result-title")
        yield Label(f"[bold]EXCEPTION[/bold] {result.exception.__class__.__name__}", id="result-subtitle")

        # Showing the sent user values
        if result.params:
            yield SectionTitle(self.localization.parameters)
            yield Label('\n'.join(f'{name}: {file}' for name, file in result.params.items()))

        if result.headers:
            yield SectionTitle(self.localization.headers)
            yield Label('\n'.join(f'{name}: {file}' for name, file in result.headers.items()))

        if result.cookies:
            yield SectionTitle(self.localization.cookies)
            yield Label('\n'.join(f'{name}: {file}' for name, file in result.cookies.items()))

        if result.files:
            yield SectionTitle(self.localization.tui_files)
            yield Label('\n'.join(f'{name}: {file}' for name, file in result.files))

        # Showing the options at the time of the request, because this might
        # the root of the issue (timeouts or SSL issues for example)
        yield SectionTitle(self.localization.tui_options)
        yield Label(f"{self.localization.tui_timeout}: {result.timeout} sec.")
        yield Label(f"{self.localization.tui_allow_redirects}: {result.allow_redirects}")
        if result.proxies:
            yield Label(f"{self.localization.tui_proxies}: {', '.join(f'{prot}: {proxy}' for prot, proxy in result.proxies.items())}")
        yield Label(f"{self.localization.tui_verify_request}: {result.verify}")
        if result.cert:
            yield Label(f"{self.localization.tui_certificate_files}: {', '.join(result.cert)}")

        # Showing a full traceback of the incident to easily debug
        # (this might take a little while to render)
        yield SectionTitle(self.localization.tui_error)
        yield Static(Traceback.from_exception(result.exception.__class__, result.exception, traceback=result.exception.__traceback__), classes="result-error-container")

    def reload_endpoint(self):
        """Reloads the request view"""
        request_view = self.query_one("#request", View)
        request_view.remove_children()
        request_view.mount_all(self.compose_request_view())
        # Making sure the request got refreshed
        request_view.refresh(layout=True)

    def compose_explorer(self):
        """
        Creates the explorer content

        Area
        ----
        ╭────────┬──────────────────────────────┬────────╮
        │        |                              |▒▒▒▒▒▒▒▒│
        │        |                              |▒▒▒▒▒▒▒▒│
        │        |                              |▒▒▒▒▒▒▒▒│
        │        |                              |▒▒▒▒▒▒▒▒│
        │        |                              |▒▒▒▒▒▒▒▒│
        │        |                              |▒▒▒▒▒▒▒▒│
        │        ├──────────────────────────────┤▒▒▒▒▒▒▒▒│
        │        |                              |▒▒▒▒▒▒▒▒│
        │        |                              |▒▒▒▒▒▒▒▒│
        ╰────────┴──────────────────────────────┴────────╯
        """
        for category, sub_categories in self.categories.items():
            # For each category, we are creating a tree, to
            # make a multi-rooted final tree.
            tree: Tree[Endpoint] = Tree(category, classes="explorer-category")
            for sub_category, endpoints in sub_categories.items():
                # An endpoint could have a category without having any sub category
                # This would cause an issue if the developer decides to use
                # `@TopLevelEndpoint` as their sub category name, which is very unlikely
                if sub_category == "@TopLevelEndpoint":
                    sub_tree = tree.root
                else:
                    sub_tree = tree.root.add(sub_category)

                # For each endpoint, add a leaf, either to the tree root, or subtree
                for endpoint in endpoints:
                    sub_tree.add_leaf(endpoint.name, endpoint)
            yield tree

    def reload_explorer(self):
        """Reloads the explorer view"""
        explorer_view = self.query_one("#tree-view", VerticalScroll)
        explorer_view.remove_children()
        explorer_view.mount_all(self.compose_explorer())
        # Making sure the explorer got refreshed
        explorer_view.refresh(layout=True)

    # pylint: disable=pointless-string-statement
    """
    ╭────────────────────────── Event Handlers ────────────────────────────────╮
    │ on_mount                                                                 │
    │ on_select_changed                                                        │
    │ on_view_clicked                                                          │
    │ on_request_view_clicked                                                  │
    │ on_result_view_clicked                                                   │
    │ on_button_pressed                                                        │
    │ on_tree_node_selected                                                    │
    │ add_file                                                                 │
    │ add_data_file                                                            │
    │ delete_file                                                              │
    │ delete_data_file                                                         │
    ╰──────────────────────────────────────────────────────────────────────────╯
    """

    def on_mount(self):
        """When mounted"""
        # Yea it's a pain to change the Header Icon
        self.query_one(Header).query_one(_header.HeaderIcon).icon = "🍡"

        # Start to update the endpoints list
        self.update_endpoints()

        # I thought I would have a problem with the mounting flow
        # because the `on_mount` method would be called before
        # drawing the DOM, thus creating a problem within `watch_endpoints`
        # but it doesn't seem to be the case ?
        # self.update_endpoints(wait=3)

    def on_select_changed(self, event: Select.Changed):
        """When a selected element is changed"""
        if event.select.id == "request-method":
            self._method = event.select.value or "*"
            self.reload_endpoint()

    def on_view_clicked(self, minimizing: str, maximizing: str):
        """When a view is clicked"""
        minimizing_element = self.query_one(f"#{minimizing}", VerticalScroll)
        maximizing_element = self.query_one(f"#{maximizing}", VerticalScroll)

        if maximizing_element.has_class("mini"):
            for element in (minimizing_element, maximizing_element):
                element.remove_class("mini")
                element.remove_class("maxi")
        else:
            maximizing_element.add_class("maxi")
            minimizing_element.add_class("mini")
            minimizing_element.remove_class("maxi")  # it normally shouldn't have this

    def on_request_view_clicked(self, event: Click):
        """When the request view is clicked"""
        self.on_view_clicked(minimizing="result", maximizing="request")

    def on_result_view_clicked(self, event: Click):
        """When the request view is clicked"""
        self.on_view_clicked(minimizing="request", maximizing="result")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """When a button is pressed"""
        # When it's an element in the request history
        if isinstance(event.button, HistoryResponse):
            # Just show the request in the `Result` panel
            self.result = event.button.response
        # When we are adding a file to the request
        if event.button.has_class("add-file-button"):
            # Show the file browser to add the file to the list
            self.push_screen(FileBrowser(localization=self.localization), self.add_file)
        # When we are adding binary data to the request
        if event.button.id == "request-data-button":
            # Show the file browser to add get the file where the data will be fetched
            self.push_screen(FileBrowser(localization=self.localization), self.add_data_file)
        # If we are resetting the endpoint
        if event.button.id == "explorer-reset":
            # Clearing the request view
            self.endpoint = None
            self.reload_endpoint()

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        """When a node is selected in a tree"""
        # Should be in the endpoints explorer tree
        if isinstance(event.node.data, Endpoint):
            self.endpoint = event.node.data
            self.reload_endpoint()

    def add_file(self, file: typing.Optional[pathlib.Path] = None):
        """Adds a file to the request"""
        if file:
            self.query_one("#request-files-container", Container).mount(FileInput(file, on_delete=self.delete_file))

    def add_data_file(self, file: typing.Optional[pathlib.Path] = None):
        """Adds the data file to the request"""
        if file:
            container = self.query_one("#request-data-container", Container)
            container.remove_children()
            container.mount(FileInput(file,
                                      on_delete=self.delete_data_file,
                                      prompt_name=False,  # data is not named
                                      id="request-data-file"))

    def delete_file(self, file_input: FileInput, file: pathlib.Path):
        """When a file is removed from the files list"""
        file_input.remove()

    def delete_data_file(self, file_input: FileInput, file: pathlib.Path):
        """When the data file is removed"""
        container = self.query_one("#request-data-container", Container)
        container.remove_children()
        container.mount(Button(self.localization.tui_add_data_file, id="request-data-button"))

    def on_url_change(self, link: str):
        """When the base URL got changed in the settings"""
        self.link = url.urlparse(str(link))
        self.update_endpoints()

    # pylint: disable=pointless-string-statement
    """
    ╭────────────────────────── Binding actions ───────────────────────────────╮
    │ action_open_options                                                      │
    │ replace_options                                                          │
    │ action_request_quit                                                      │
    │ action_toggle_history                                                    │
    │ action_toggle_results                                                    │
    │ action_toggle_explorer                                                   │
    │ action_submit                                                            │
    │ request_worker                                                           │
    │ add_result                                                               │
    ╰──────────────────────────────────────────────────────────────────────────╯
    """

    def action_open_options(self):
        """When the user wants to see the options screen"""
        self.push_screen(HTTPOptionsScreen(base_url=url.urlunparse(self.link),
                                           on_url_change=self.on_url_change,
                                           options=self.options,
                                           id="options-screen",
                                           localization=self.localization),
                         self.replace_options)

    def replace_options(self, options: HTTPOptions):
        """To replace the current options"""
        self.options = options
        HTTPOptionsScreen.dumps("http", options)
        self.localization = language_to_localization(self.options.language)

    def action_request_quit(self) -> None:
        """Action to display the quit dialog."""
        self.push_screen(QuitScreen(localization=self.localization))

    def action_toggle_history(self):
        """Called when the user fires the `toggle_history` action"""
        self.toggle_history = not self.toggle_history

    def action_toggle_results(self):
        """Called when the user fires the `toggle_results` action"""
        self.toggle_results = not self.toggle_results

    def action_toggle_explorer(self):
        """Called when the user fires the `toggle_explorer` action"""
        self.toggle_explorer = not self.toggle_explorer

    def action_submit(self):
        """Called when the user submitted the request"""
        method = self.query_one("#request-method", Select).value or "*"
        path = url.urlparse(self.query_one("#request-path", Input).value)
        final_path = url.urlunparse((
            # Defaulting to the registered base URL
            path.scheme or self.link.scheme,
            path.netloc or self.link.netloc,
            path.path,
            path.params,
            path.query,
            path.fragment
        ))

        params = self.query_one("#request-parameters", UserSentForm).values

        # Setting a custom user agent by default
        headers = {
            "User-Agent": f"nasse-http/{__info__.__version__}"
        }
        # Which can be overwritten here
        headers.update(self.query_one("#request-headers", UserSentForm).values)

        cookies = self.query_one("#request-cookies", UserSentForm).values

        self.result = Loading(url=final_path)

        files = []
        for file_input in self.query_one("#request-files-container", Container).query(FileInput):
            files.append((file_input.input_name or "file", (file_input.file.name, file_input.file.open("rb"))))

        try:
            data = self.query_one("#request-data-file", FileInput).file.read_bytes()
        except Exception:
            data = None

        self.request_worker(method, final_path, params, headers, cookies, files, data)

    @work(exclusive=True)
    def request_worker(self,
                       method: str,
                       final_path: str,
                       params: typing.Dict[str, typing.List[str]],
                       headers: typing.Dict[str, str],
                       cookies: typing.Dict[str, str],
                       files: typing.List[typing.Tuple[str, typing.Tuple[str, typing.BinaryIO]]],
                       data: typing.Optional[bytes] = None):
        """The worker thread which actually makes the request"""
        worker = get_current_worker()
        try:
            if not self.options.cert:
                cert = None
            elif len(self.options.cert) == 1:
                cert = self.options.cert[0]
            else:
                # it can't exceed two files
                cert = (self.options.cert[0], self.options.cert[1])
            response = requests.request(method,
                                        final_path,
                                        params=params,
                                        headers=headers,
                                        cookies=cookies,
                                        files=files,
                                        data=data,
                                        timeout=self.options.timeout,
                                        allow_redirects=self.options.allow_redirects,
                                        verify=self.options.verify,
                                        proxies=self.options.proxies,
                                        cert=cert)
        except Exception as exc:
            response = Error(exception=exc,
                             method=method,
                             url=final_path,
                             params=params,
                             headers=headers,
                             cookies=cookies,
                             files=[(name, element[0]) for name, element in files],
                             data=data,
                             timeout=self.options.timeout,
                             allow_redirects=self.options.allow_redirects,
                             verify=self.options.verify,
                             proxies=self.options.proxies,
                             cert=self.options.cert)

        if not worker.is_cancelled:
            self.call_from_thread(self.add_result, response)
            # Opening up the result panel if we got a result
            self.toggle_results = True

    def add_result(self, response: typing.Union[requests.Response, Error]):
        """Adds the given response to the results"""
        self.history = [*self.history, response]
        self.result = response

    # pylint: disable=pointless-string-statement
    """
    ╭──────────────────────── Reactive handlers ────────────────────────────╮
    │ watch_localization                                                    │
    │ watch_endpoints                                                       │
    │ watch_toggle_history                                                  │
    │ watch_toggle_results                                                  │
    │ watch_toggle_explorer                                                 │
    │ watch_history                                                         │
    │ watch_result                                                          │
    ╰───────────────────────────────────────────────────────────────────────╯
    """

    def watch_localization(self, localization: typing.Type[Localization]) -> None:
        """Called when `localization` is modified"""
        # self.refresh(repaint=True, layout=True)
        self.app.exit()
        self.app.run()

    def watch_endpoints(self, endpoints: typing.List[Endpoint]) -> None:
        """Called when `endpoints` is modified"""
        try:
            self.reload_explorer()
        except Exception:
            # print("Couldn't reload the explorer")
            pass

    def watch_toggle_history(self, toggle_history: bool) -> None:
        """Called when `toggle_history` is modified"""
        self.query_one("#history", Container).set_class(not toggle_history, "unload")

    def watch_toggle_results(self, toggle_results: bool) -> None:
        """Called when `toggle_results` is modified"""
        self.query_one("#result", VerticalScroll).set_class(not toggle_results, "unload")
        self.query_one("#request", VerticalScroll).set_class(not toggle_results, "full")

    def watch_toggle_explorer(self, toggle_explorer: bool) -> None:
        """Called when `toggle_explorer` is modified"""
        self.query_one("#explorer", Container).set_class(not toggle_explorer, "unload")

    def watch_history(self, history: typing.List[requests.Response]) -> None:
        """Called when `history` is modified"""
        # Avoiding to store too much things in the request history
        # because each one of them is rendered in the history panel
        self.history = history[-(self.options.history_limit - 1):]
        try:
            self.query_one(series.TimeSeries).series = [resp.elapsed.total_seconds() * 1000  # measured in ms
                                                        for resp in history if isinstance(resp, requests.Response)]
            history_requests = self.query_one("#history-requests", VerticalScroll)
            history_requests.remove_children()
            history_requests.mount_all([HistoryResponse(element) for element in reversed(history)])
        except Exception:
            pass

    def watch_result(self, result: typing.Optional[requests.Response]):
        """Called when `result` is modified"""
        container = self.query_one("#result", VerticalScroll)
        container.remove_children()
        container.mount(StickyHeader(self.localization.tui_result))

        if result is None:
            return container.mount_all(self.compose_result_start())
        if isinstance(result, Loading):
            return container.mount_all(self.compose_result_loading(result))
        if isinstance(result, Error):
            return container.mount_all(self.compose_result_error(result))

        return container.mount_all(self.compose_result_response(result))

# Made this path suggestion thing, which searches
# its suggestions in the request history but doesn't seem to
# work well and I don't really know why


class PathSuggestion(Suggester):
    """Gives HTTP path suggestions"""

    def __init__(self, app: HTTP) -> None:
        super().__init__(use_cache=False, case_sensitive=False)
        self.app = app

    async def get_suggestion(self, value: str) -> typing.Optional[str]:
        """Gets a completion from the given possibilities.

        Args:
            value: The current value.

        Returns:
            A valid completion suggestion or `None`.
        """
        for element in self.app.history:
            path = url.urlparse(element.url).path
            if value.startswith(path):
                return path
        return None


if __name__ == "__main__":
    # HTTP("https://google.com").run()
    # HTTP("https://eosqyydyun9tw26.m.pipedream.net").run()
    # HTTP("http://httpbin.org/get", endpoints=[
    #     Endpoint(name="GET request", category="Method Requests", sub_category="GET", methods="GET",
    #              description="This is a GET request", headers=[UserSent("X-NASSE-TEST", description="This is a test")], path="/get"),
    #     Endpoint(name="POST request", category="Method Requests", sub_category="POST", methods="POST",
    #              description="This is a POST request", headers=[UserSent("X-NASSE-TEST", description="This is a test")], parameters=UserSent("hello", description="world"), path="/post"),
    #     Endpoint(name="Multiple request", category="Method Requests", methods="*",
    #              description={"GET": "This is a multiple methods request", "POST": "This is really cool", "*": "Yup as expected"}, headers=[UserSent("X-NASSE-TEST", description="This is a test")], parameters={"POST": UserSent("hello", description="world")}, path="/post"),
    # ] * 20).run()
    HTTP("").run()
