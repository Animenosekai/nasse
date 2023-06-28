"""Makes HTTP requests"""
import dataclasses
import json
import typing
import urllib.parse as url

import requests
from rich.traceback import Traceback
from textual import events
from textual.containers import Container, Horizontal, VerticalScroll
from textual.reactive import reactive, var
from textual.screen import ModalScreen
from textual.suggester import Suggester
from textual.validation import Number
from textual.widgets import (Button, Footer, Header, Input, Label, Pretty,
                             Select, Switch, _header, Static)

from nasse.docs.localization import EnglishLocalization, Localization
from nasse.models import StandardMethod
from nasse.tui.app import App
from nasse.tui.components import series
from nasse.tui.components.forms import UserSentForm
from nasse.tui.components.headers import StickyHeader
from nasse.tui.components.history import HistoryResponse
from nasse.tui.components.texts import SectionTitle
from nasse.tui.error import Error

HISTORY_LIMIT = 10


@dataclasses.dataclass
class Options:
    """App options"""
    timeout: float = 10
    allow_redirects: bool = True
    proxies: typing.Dict[str, str] = dataclasses.field(default_factory=dict)
    verify: bool = True
    # cert
    # stream
    # hooks


class OptionsScreen(ModalScreen[Options]):
    """The options managing screen"""

    DEFAULT_CSS = """
    OptionsScreen {
        align: center middle;
        background: rgba(30, 30, 30, 0.75);
    }

    #options-timeout {
        margin-bottom: 1;
    }

    .options-switch-title {
        content-align: center middle;
        height: 3;
        content-align: center middle;
        width: 20;
    }

    .options-switch-container {
        align-vertical: middle;
        margin-bottom: 1;
        height: auto;
        width: auto;
    }

    #options-container {
        height: auto;
        width: 25w;
        padding: 2 10;
        border: round gray
    }


    #modal-confirmation-container {
        width: auto;
        height: auto;
        dock: bottom;
        align-horizontal: right;
    }
    """

    def __init__(self,
                 options: Options = None,
                 name: typing.Optional[str] = None,
                 id: typing.Optional[str] = None,
                 classes: typing.Optional[str] = None) -> None:
        super().__init__(name, id, classes)
        self.options = options or Options()

    def compose(self):
        yield StickyHeader("Options")
        with VerticalScroll(id="options-container"):
            yield SectionTitle("Timeout")
            yield Input(str(self.options.timeout),
                        placeholder="timeout (sec.)",
                        validators=[Number(minimum=0.0)],
                        id="options-timeout")

            yield Horizontal(
                Label("Allow Redirects", id="options-redirects-title", classes="options-switch-title"),
                Switch(value=self.options.allow_redirects, id="options-redirects-switch"),
                id="options-redirects-container",
                classes="options-switch-container"
            )

            yield Horizontal(
                Label("Verify Request", id="options-verify-title", classes="options-switch-title"),
                Switch(value=self.options.allow_redirects, id="options-verify-switch"),
                id="options-verify-container",
                classes="options-switch-container"
            )

        with Horizontal(id="modal-confirmation-container"):
            yield Button("Ok")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """When a button is pressed"""
        options = dataclasses.asdict(self.options)
        options.update({
            "timeout": float(self.query_one("#options-timeout", Input).value),
            "allow_redirects": self.query_one("#options-redirects-switch", Switch).value,
            "verify": self.query_one("#options-verify-switch", Switch).value,
        })
        return self.dismiss(Options(**options))

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            return self.dismiss(self.options)


class HTTP(App):
    """Lets you make HTTP requests comfortably"""

    CSS_PATH = "../styles/http.css"

    history: reactive[typing.List[requests.Response]] = reactive(list)
    toggle_history = var(True)
    toggle_results = var(False)
    result: reactive[typing.Optional[requests.Response]] = reactive(None)

    BINDINGS = [("h", "toggle_history", "History"), ("r", "toggle_results", "Result"), ("s", "submit", "Submit"), ("o", "open_options", "Options")]

    def __init__(self, link: str, localization: Localization = EnglishLocalization, options: typing.Optional[Options] = None, **kwargs):
        super().__init__(**kwargs)
        self.link = url.urlparse(link)
        self.localization = localization

        try:
            with open(".http.nasse.config", "r") as f:
                saved_options = Options(**json.loads(f.read()))
        except Exception:
            saved_options = Options()

        self.options = options or saved_options

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
                with VerticalScroll(id="request"):
                    # Requests Options
                    yield StickyHeader("Request")

                    with Horizontal(id="request-path-container"):
                        yield Select([(method, method) for method in typing.get_args(StandardMethod)], allow_blank=False, value="GET", id="request-method")
                        yield Input("/", placeholder="path", suggester=PathSuggestion(self), id="request-path")

                    yield UserSentForm("Parameters", multiple=True, id="request-parameters")
                    yield UserSentForm("Headers", id="request-headers")
                    yield UserSentForm("Cookies", id="request-cookies")

                    # data
                    # files
                with VerticalScroll(id="result"):
                    # Request Result
                    yield StickyHeader("Result")
                    yield Label("Start by making a request", id="empty-result-label")

        yield Footer()

    def on_mount(self):
        """When mounted"""
        self.query_one(Header).query_one(_header.HeaderIcon).icon = "🍡"

    def on_button_pressed(self, event: HistoryResponse.Pressed) -> None:
        """When a button is pressed"""
        if isinstance(event.button, HistoryResponse):
            self.result = event.button.response

    # def action_test(self):
    #     """Testing URL"""
    #     self.history = [*self.history, requests.get(self.url, timeout=100)]

    def action_toggle_history(self):
        """Called when the user fires the `toggle_history` action"""
        self.toggle_history = not self.toggle_history

    def action_toggle_results(self):
        """Called when the user fires the `toggle_history` action"""
        self.toggle_results = not self.toggle_results

    def action_submit(self):
        """Called when the user submitted the request"""
        method = self.query_one("#request-method", Select).value
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
            "User-Agent": "nasse-http/1.0.0"
        }
        headers.update(self.query_one("#request-headers", UserSentForm).values)

        cookies = self.query_one("#request-cookies", UserSentForm).values

        try:
            response = requests.request(method,
                                        final_path,
                                        params=params,
                                        headers=headers,
                                        cookies=cookies,
                                        timeout=self.options.timeout,
                                        allow_redirects=self.options.allow_redirects,
                                        verify=self.options.verify)
        except Exception as exc:
            response = Error(method=method,
                             url=final_path,
                             exception=exc,
                             params=params,
                             headers=headers,
                             cookies=cookies)
        self.history = [*self.history, response]
        self.result = response

    def action_open_options(self):
        """When the user wants to see the options screen"""
        self.push_screen(OptionsScreen(self.options), self.replace_options)

    def replace_options(self, options: Options):
        """To replace the current options"""
        self.options = options
        with open(".http.nasse.config", "w", encoding="utf-8") as f:
            f.write(json.dumps(dataclasses.asdict(options), ensure_ascii=False, separators=(",", ":")))

    def watch_toggle_history(self, toggle_history: bool) -> None:
        """Called when `toggle_history` is modified"""
        self.query_one("#history", Container).set_class(not toggle_history, "unload")

    def watch_toggle_results(self, toggle_results: bool) -> None:
        """Called when `toggle_results` is modified"""
        self.query_one("#result", VerticalScroll).set_class(not toggle_results, "unload")
        self.query_one("#request", VerticalScroll).set_class(not toggle_results, "full")

    def watch_history(self, history: typing.List[requests.Response]) -> None:
        """Called when `history` is modified"""
        self.history = history[-HISTORY_LIMIT:]
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

        yield SectionTitle("Parameters")
        yield Pretty(result.params)

        yield SectionTitle("Headers")
        yield Pretty(result.headers)

        yield SectionTitle("Cookies")
        yield Pretty(result.cookies)

        yield SectionTitle("Error")
        yield Static(Traceback.from_exception(result.exception.__class__, result.exception, traceback=result.exception.__traceback__))

    def compose_result(self, result: requests.Response):
        """Creates the result view"""
        yield Label(f"{result.request.method} {result.url}", id="result-title")
        yield Label(f"[bold]{result.status_code}[/bold] {result.reason} [grey]in {series.transform_time(result.elapsed.total_seconds() * 1000)}[/grey]", id="result-subtitle")

        yield SectionTitle("Headers")
        yield Pretty(result.headers)

        yield SectionTitle("Cookies")
        yield Pretty(result.cookies)

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

    def watch_result(self, result: typing.Optional[requests.Response]):
        """Called when `result` is modified"""
        container = self.query_one("#result", VerticalScroll)
        container.remove_children()
        container.mount(StickyHeader("Result"))
        if result is None:
            return container.mount(Label("Start by making a request", id="empty-result-label"))
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
    HTTP("https://eosqyydyun9tw26.m.pipedream.net").run()
    # HTTP("http://httpbin.org/get").run()
