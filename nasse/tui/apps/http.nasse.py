"""Makes HTTP requests

TODO
----
- Profiles
"""
import dataclasses
import pathlib
import typing
import urllib.parse as url

import requests
from rich.traceback import Traceback
from textual import work
from textual.containers import Container, Horizontal, VerticalScroll
from textual.binding import Binding
from textual.events import Click
from textual.reactive import reactive, var
from textual.suggester import Suggester
from textual.validation import Integer, Number
from textual.widgets import (Button, Footer, Header, Input, Label,
                             LoadingIndicator, Pretty, Select, Static, Switch, Tree,
                             _header)
from textual.worker import get_current_worker

from nasse.docs.localization import EnglishLocalization, Localization
from nasse.models import Types, UserSent, Endpoint, get_method_variant
from nasse.tui.app import App
from nasse.tui.components import series
from nasse.tui.components.forms import UserSentForm
from nasse.tui.components.headers import StickyHeader
from nasse.tui.components.history import HistoryResponse
from nasse.tui.components.texts import SectionTitle
from nasse.tui.error import Error
from nasse.tui.screens import FileBrowser, OptionsScreen, QuitScreen
from nasse.tui.widget import Widget
from nasse import __info__


# @dataclasses.dataclass
# class Profile:
#     """A profile"""
#     name: str
#     parameters: typing.Dict[str, typing.List[str]] = dataclasses.field(default_factory=dict)
#     headers: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
#     cookies: typing.Dict[str, str] = dataclasses.field(default_factory=dict)


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
                 **kwargs):
        self.file = pathlib.Path(file)
        self.on_delete = on_delete
        self.prompt_name = prompt_name
        super().__init__(**kwargs)

    def compose(self):
        elements = []
        if self.prompt_name:
            elements.append(Input(placeholder="Name", classes="file-name"))
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


class View(VerticalScroll):
    """A view in the main screen"""

    def __init__(self, on_click: typing.Callable[[Click], typing.Any], **kwargs) -> None:
        super().__init__(**kwargs)
        self.when_clicked = on_click

    def on_click(self, event: Click):
        return self.when_clicked(event)


@dataclasses.dataclass
class HTTPOptions:
    """App options"""
    timeout: float = 10
    allow_redirects: bool = True
    proxies: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    verify: bool = True
    cert: typing.List[str] = dataclasses.field(default_factory=list)
    history_limit: int = 10
    # profiles: typing.List[Profile] = dataclasses.field(default_factory=list)
    # stream
    # hooks


class HTTPOptionsScreen(OptionsScreen[HTTPOptions]):
    """The HTTP app options screen"""

    def compose_options(self):
        """Composes the inner options view"""
        with VerticalScroll(id="options-inner-container"):
            yield SectionTitle("History Limit")
            yield Input(str(self.options.history_limit),
                        placeholder="maximum number of requests in the history",
                        validators=[Integer(minimum=0, failure_description="The limit must be a positive integer")],
                        id="options-history-limit")

            yield SectionTitle("Timeout")
            yield Input(str(self.options.timeout),
                        placeholder="timeout (sec.)",
                        validators=[Number(minimum=0.0, failure_description="The timeout must be a positive number")],
                        id="options-timeout")

            yield SectionTitle("Redirects")
            yield Horizontal(
                Label("Allow Redirects", id="options-redirects-title", classes="options-switch-title"),
                Switch(value=self.options.allow_redirects, id="options-redirects-switch"),
                id="options-redirects-container",
                classes="options-switch-container"
            )

            yield UserSentForm("Proxies", id="options-proxies", initial_values=[(UserSent(name=key), value) for key, value in self.options.proxies.items()])

            yield SectionTitle("Security")
            yield Horizontal(
                Label("Verify Request", id="options-verify-title", classes="options-switch-title"),
                Switch(value=self.options.verify, id="options-verify-switch"),
                id="options-verify-container",
                classes="options-switch-container"
            )

            with Container(id="certificate-files", classes="files-input-container"):
                with Container(id="certificate-files-container", classes="files-container"):
                    for file in self.options.cert:
                        yield FileInput(pathlib.Path(file), self.delete_cert_file, prompt_name=False)
                yield Button("Add certificate", id="add-certificate-button", classes="add-file-button")

    def collect_values(self) -> typing.Dict[str, typing.Any]:
        """Collect the different options value"""
        return {
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


@dataclasses.dataclass
class Loading:
    """The request loading state"""
    url: str


class HTTP(App):
    """Lets you make HTTP requests comfortably"""

    CSS_PATH = "../styles/http.css"

    history: reactive[typing.List[typing.Union[requests.Response, Error]]] = reactive(list)
    toggle_history = var(True)
    toggle_results = var(False)
    toggle_explorer = var(False)
    result: reactive[typing.Optional[typing.Union[requests.Response, Error, Loading]]] = reactive(None)
    endpoint: reactive[typing.Optional[Endpoint]] = reactive(None)
    method: reactive[Types.Method.Any] = reactive("*")
    # profile: reactive[str] = reactive("Default")

    BINDINGS = [("h", "toggle_history", "History"), ("r", "toggle_results", "Result"), ("e", "toggle_explorer", "Explorer"),
                ("s", "submit", "Submit"), ("o", "open_options", "Options"), ("q", "request_quit", "Quit"), Binding("escape", "request_quit", "Quit", show=False)]

    def __init__(self,
                 link: str,
                 endpoints: typing.Optional[typing.List[Endpoint]] = None,
                 localization: typing.Union[Localization, typing.Type[Localization]] = EnglishLocalization,
                 options: typing.Optional[HTTPOptions] = None,
                 **kwargs):
        super().__init__(**kwargs)
        self.link = url.urlparse(link)
        self.localization = localization
        self.endpoints = endpoints or []

        self.options = options or HTTPOptionsScreen.loads("http", HTTPOptions)

    def compose(self):
        yield Header(show_clock=True)

        # Screen
        with Horizontal(id="screen"):
            with Container(id="history"):
                # History
                yield StickyHeader("History")
                with VerticalScroll(id="history-requests"):
                    # Requests History
                    for response in self.history:
                        yield HistoryResponse(response)
                yield series.TimeSeries([], id="history-ping")
            with Container(id="main"):
                # Main Page
                # Requests Options
                yield StickyHeader("Request", id="request-title")

                with View(id="request", on_click=self.on_request_view_clicked):
                    yield from self.compose_request_view()

                with View(id="result", on_click=self.on_result_view_clicked):
                    # Request Result
                    yield StickyHeader("Result")
                    yield Label("Start by making a request", id="empty-result-label")

            with Container(id="explorer"):
                # Endpoints explorer
                # Only for servers running Nasse
                yield StickyHeader("Explorer")
                yield Button("Reset", id="explorer-reset")
                with VerticalScroll(id="endpoints-explorer"):
                    with VerticalScroll(id="tree-view"):
                        for category, sub_categories in self.categories.items():
                            tree: Tree[Endpoint] = Tree(category)
                            # tree.root.expand()
                            for sub_category, endpoints in sub_categories.items():
                                if sub_category == "@TopLevelEndpoint":
                                    sub_tree = tree.root
                                else:
                                    sub_tree = tree.root.add(sub_category)
                                for endpoint in endpoints:
                                    sub_tree.add_leaf(endpoint.name, endpoint)
                            yield tree
        yield Footer()

    def compose_request_view(self):
        """Creates the request view"""

        method = self._method

        if self.endpoint:
            description = self.endpoint.description.get(method, self.endpoint.description.get("*", self.localization.no_description))
            yield Container(
                Label(self.endpoint.name, id="request-information-title"),
                Label(description, id="request-information-description"),
                id="request-information"
            )

        if not self.endpoint or not self.endpoint.methods or "*" in self.endpoint.methods:
            request_select = Select([(method, method) for method in typing.get_args(Types.Method.Standard)],
                                    allow_blank=False, value=method if method != "*" else "GET", id="request-method")
        else:
            request_select = Select([(method, method) for method in self.endpoint.methods],
                                    allow_blank=False, value=method, id="request-method")

        if self.endpoint:
            request_input = Input(self.endpoint.path, placeholder="path", suggester=PathSuggestion(self), id="request-path")
        else:
            request_input = Input("/", placeholder="path", suggester=PathSuggestion(self), id="request-path")

        yield Horizontal(request_select, request_input, id="request-path-container")

        yield Container(UserSentForm("Parameters", inputs=get_method_variant(method, self.endpoint.parameters)
                                     if self.endpoint else None, multiple=True, id="request-parameters"),
                        UserSentForm("Headers", inputs=get_method_variant(method, self.endpoint.headers)
                                     if self.endpoint else None, id="request-headers"),
                        UserSentForm("Cookies", inputs=get_method_variant(method, self.endpoint.cookies)
                                     if self.endpoint else None, id="request-cookies"),
                        id="request-user-sent")

        yield SectionTitle("File")
        yield Container(Container(id="request-files-container", classes="files-container"),
                        Button("Add file", classes="add-file-button"),
                        classes="files-input-container")

        yield SectionTitle("Data")
        yield Container(Button("Add data file", id="request-data-button"), id="request-data-container")

    @property
    def _method(self) -> str:
        """Get the currently selected method"""
        if self.method == "*":
            try:
                return next(iter(self.endpoint.methods))
            except Exception:
                return "*"
        else:
            return self.method

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

    def on_mount(self):
        """When mounted"""
        self.query_one(Header).query_one(_header.HeaderIcon).icon = "🍡"

    def on_select_changed(self, event: Select.Changed):
        """When a selected element is changed"""
        if event.select.id == "request-method":
            self.method = event.select.value or "*"
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
            minimizing_element.remove_class("maxi")

    def on_request_view_clicked(self, event: Click):
        """When the request view is clicked"""
        self.on_view_clicked(minimizing="result", maximizing="request")

    def on_result_view_clicked(self, event: Click):
        """When the request view is clicked"""
        self.on_view_clicked(minimizing="request", maximizing="result")

    def reload_endpoint(self):
        """Reloads the request view"""
        request_view = self.query_one("#request", View)
        recompose = self.compose_request_view()
        request_view.remove_children()
        request_view.mount_all(recompose)
        request_view.refresh(layout=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """When a button is pressed"""
        if isinstance(event.button, HistoryResponse):
            self.result = event.button.response
        if event.button.has_class("add-file-button"):
            self.push_screen(FileBrowser(), self.add_file)
        if event.button.id == "request-data-button":
            self.push_screen(FileBrowser(), self.add_data_file)
        if event.button.id == "explorer-reset":
            self.endpoint = None
            self.reload_endpoint()

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        """When a node is selected in a tree"""
        if isinstance(event.node.data, Endpoint):
            self.endpoint = event.node.data
            self.reload_endpoint()

    def add_file(self, file: typing.Optional[pathlib.Path] = None):
        """Adds a file to the request"""
        if file:
            self.query_one("#request-files-container", Container).mount(FileInput(file, self.delete_file))

    def add_data_file(self, file: typing.Optional[pathlib.Path] = None):
        if file:
            container = self.query_one("#request-data-container", Container)
            container.remove_children()
            container.mount(FileInput(file, self.delete_data_file, prompt_name=False, id="request-data-file"))

    def delete_file(self, file_input: FileInput, file: pathlib.Path):
        """When a file is removed from the files list"""
        file_input.remove()

    def delete_data_file(self, file_input: FileInput, file: pathlib.Path):
        """When the data file is removed"""
        container = self.query_one("#request-data-container", Container)
        container.remove_children()
        container.mount(Button("Add data file", id="request-data-button"))

    def action_open_options(self):
        """When the user wants to see the options screen"""
        self.push_screen(HTTPOptionsScreen(self.options, id="options-screen"), self.replace_options)

    def action_request_quit(self) -> None:
        """Action to display the quit dialog."""
        self.push_screen(QuitScreen())

    def replace_options(self, options: HTTPOptions):
        """To replace the current options"""
        self.options = options
        HTTPOptionsScreen.dumps("http", options)

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
            path.scheme or self.link.scheme,
            path.netloc or self.link.netloc,
            path.path,
            path.params,
            path.query,
            path.fragment
        ))

        params = self.query_one("#request-parameters", UserSentForm).values

        headers = {
            "User-Agent": f"nasse-http/{__info__.__version_string__()}"
        }
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
            self.toggle_results = True

    def add_result(self, response: typing.Union[requests.Response, Error]):
        """Adds the given response to the results"""
        self.history = [*self.history, response]
        self.result = response

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
        self.history = history[-(self.options.history_limit - 1):]
        try:
            self.query_one(series.TimeSeries).series = [resp.elapsed.total_seconds() * 1000
                                                        for resp in history if isinstance(resp, requests.Response)]
            history_requests = self.query_one("#history-requests", VerticalScroll)
            history_requests.remove_children()
            history_requests.mount_all([HistoryResponse(element) for element in reversed(history)])
        except Exception:
            pass

    def compose_result_error(self, result: Error):
        """Creates the result view"""
        yield Label(f"{result.method} {result.url}", id="result-title")
        yield Label(f"[bold]EXCEPTION[/bold] {result.exception.__class__.__name__}", id="result-subtitle")

        if result.params:
            yield SectionTitle("Parameters")
            yield Label('\n'.join(f'{name}: {file}' for name, file in result.params.items()))
        # yield Pretty(result.params)

        if result.headers:
            yield SectionTitle("Headers")
            yield Label('\n'.join(f'{name}: {file}' for name, file in result.headers.items()))
        # yield Pretty(result.headers)

        if result.cookies:
            yield SectionTitle("Cookies")
            yield Label('\n'.join(f'{name}: {file}' for name, file in result.cookies.items()))
        # yield Pretty(result.cookies)

        if result.files:
            yield SectionTitle("Files")
            yield Label('\n'.join(f'{name}: {file}' for name, file in result.files))

        yield SectionTitle("Options")
        yield Label(f"Timeout: {result.timeout} sec.")
        yield Label(f"Allow Redirects: {result.allow_redirects}")
        if result.proxies:
            yield Label(f"Proxies: {', '.join(f'{prot}: {proxy}' for prot, proxy in result.proxies.items())}")
        yield Label(f"Verify Request: {result.verify}")
        if result.cert:
            yield Label(f"Certificate Files: {', '.join(result.cert)}")

        yield SectionTitle("Error")
        yield Static(Traceback.from_exception(result.exception.__class__, result.exception, traceback=result.exception.__traceback__), classes="result-error-container")

    def compose_result(self, result: requests.Response):
        """Creates the result view"""
        yield Label(f"{result.request.method} {result.url}", id="result-title")
        yield Label(f"[bold]{result.status_code}[/bold] {result.reason} [grey]in {series.transform_time(result.elapsed.total_seconds() * 1000)}[/grey]", id="result-subtitle")

        if result.headers:
            yield SectionTitle("Headers")
            yield Label('\n'.join(f'{name}: {file}' for name, file in result.headers.items()))
        # yield Pretty(result.headers)

        if result.cookies:
            yield SectionTitle("Cookies")
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
                content = "[red](ERROR)[/red] Can't display the content"

        yield SectionTitle("Content")
        yield Pretty(content, id="result-content")

    def compose_start(self):
        """Creates the start view"""
        yield Label("Start by making a request", id="empty-result-label")

    def compose_loading(self, result: Loading):
        """Creates loading view"""
        yield Container(
            Horizontal(
                Label("🧑‍💻"),
                LoadingIndicator(),
                Label("🌐"),
                id="loading-container"
            ),
            Label(f"Contacting {url.urlparse(result.url).netloc}"),
            id="loading-view"
        )

    def watch_result(self, result: typing.Optional[requests.Response]):
        """Called when `result` is modified"""
        container = self.query_one("#result", VerticalScroll)
        container.remove_children()
        container.mount(StickyHeader("Result"))

        if result is None:
            return container.mount_all(self.compose_start())
        if isinstance(result, Loading):
            return container.mount_all(self.compose_loading(result))
        if isinstance(result, Error):
            return container.mount_all(self.compose_result_error(result))

        return container.mount_all(self.compose_result(result))


class PathSuggestion(Suggester):
    """Gives HTTP path suggestions"""

    def __init__(self, app: HTTP) -> None:
        super().__init__(use_cache=False, case_sensitive=False)
        self.app = app

    async def get_suggestion(self, value: str) -> str | None:
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
    HTTP("http://httpbin.org/get", endpoints=[
        Endpoint(name="GET request", category="Method Requests", sub_category="GET", methods="GET",
                 description="This is a GET request", headers=[UserSent("X-NASSE-TEST", description="This is a test")], path="/get"),
        Endpoint(name="POST request", category="Method Requests", sub_category="POST", methods="POST",
                 description="This is a POST request", headers=[UserSent("X-NASSE-TEST", description="This is a test")], parameters=UserSent("hello", description="world"), path="/post"),
        Endpoint(name="Multiple request", category="Method Requests", methods="*",
                 description={"GET": "This is a multiple methods request", "POST": "This is really cool", "*": "Yup as expected"}, headers=[UserSent("X-NASSE-TEST", description="This is a test")], parameters={"POST": UserSent("hello", description="world")}, path="/post"),
    ]).run()
