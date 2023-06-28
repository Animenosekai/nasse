"""The Nasse Endpoints Browser TUI"""

import hashlib
import typing
from typing import Type

from rich.syntax import Syntax
from textual import events
from textual.app import App, ComposeResult, CSSPathType
from textual.binding import _Bindings
from textual.containers import Horizontal, VerticalScroll
from textual.driver import Driver
from textual.reactive import reactive, var
from textual.widget import Widget
from textual.widgets import (Button, ContentSwitcher, Footer, Header, Input,
                             Label, Select, Static, TabbedContent, Tree)

from nasse import Endpoint, UserSent, models
from nasse.docs import curl, javascript, python
from nasse.docs.localization import (EnglishLocalization, JapaneseLocalization,
                                     Localization)


def hash_endpoint(endpoint: Endpoint):
    """Hashes the given endpoint"""
    digest = hashlib.sha256(endpoint.path.encode() + endpoint.name.encode() + endpoint.category.encode() + endpoint.sub_category.encode()).hexdigest()
    while digest[0].isdigit():
        digest = digest[1:]
    return digest


class Section(Widget):
    pass


class UserSentInput(Widget):
    """The input component for a user sent value"""
    value: reactive[typing.Optional[UserSent]] = reactive(None)

    def __init__(self, value: typing.Optional[UserSent] = None, values: typing.Optional[typing.Set[UserSent]] = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.value = value
        self.values = values or set()

    def compose(self) -> ComposeResult:
        with Horizontal() as container:
            container.styles.height = "auto"
            if not self.value:
                non_required = [(element.name, element) for element in self.values if not element.required]
                if non_required:
                    yield Select(non_required)
                    yield Input(disabled=True)
                return
            yield Select([(element.name, element) for element in self.values], value=self.value, disabled=self.value.required)
            yield Input(placeholder=self.value.type.__name__ if hasattr(self.value.type, "__name__") else str(self.value.type))
        label = Label(self.value.description)
        label.styles.text_opacity = "50%"
        yield label


class UserSentForm(Widget):
    """A form with all of the user sent values"""

    def __init__(self, inputs: typing.Set[UserSent], *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.inputs = inputs

    def compose(self) -> ComposeResult:
        for element in self.inputs:
            if element.required:
                yield UserSentInput(element, values=self.inputs)

        yield UserSentInput(None, self.inputs)

        with Horizontal() as container:
            container.styles.align_horizontal = "right"
            container.styles.height = "auto"
            button = Button("Add")
            button.styles.background = "blue"
            button.styles.color = "white"
            yield button
            yield Button("Remove")


class EndpointWindow(Widget):
    """An endpoint details window"""
    endpoint: typing.Optional[Endpoint] = None
    method: models.Method = "*"

    def __init__(self, endpoints: typing.List[Endpoint], localization: Localization = EnglishLocalization, **kwargs) -> None:
        super().__init__(**kwargs)
        self.localization = localization
        self.endpoints = endpoints

    def load_endpoint(self, endpoint: typing.Optional[Endpoint] = None):
        """Loads the given endpoint"""
        self.query().first(ContentSwitcher).current = hash_endpoint(endpoint)

    def compose(self) -> ComposeResult:
        with ContentSwitcher(initial="welcome-button"):
            yield Button("Start by selecting an endpoint", id="welcome-button")
            for endpoint in self.endpoints:
                with VerticalScroll(id=hash_endpoint(endpoint)):
                    description = endpoint.description.get(self.method, endpoint.description.get("*"))
                    if description is None:
                        description = self.localization.no_description
                    yield Label(f"[bold]{description}[/bold]", classes="blockquote")

                    with Horizontal() as container:
                        container.styles.height = "auto"
                        if self.method == "*":
                            yield Select([(arg, arg) for arg in typing.get_args(models.StandardMethod)], prompt="Method", allow_blank=False, value="GET")
                        else:
                            yield Select([(self.method, self.method)], value=self.method, disabled=True)
                        yield Input(endpoint.path, disabled=True)

                    for title, element in [(self.localization.parameters, endpoint.parameters),
                                           (self.localization.headers, endpoint.headers),
                                           (self.localization.cookies, endpoint.cookies),
                                           (self.localization.dynamic_url, endpoint.dynamics)]:
                        values = models.get_method_variant(self.method, element)
                        if values:
                            yield Label(f"[underline]{title}[/underline]")
                            yield UserSentForm(values)

                    yield Label(f"[underline]{self.localization.example}[/underline]")
                    with TabbedContent("Python", "JavaScript", "cURL"):
                        yield Static(Syntax(python.create_python_example_for_method(endpoint, self.method),
                                            "python",
                                            line_numbers=True,
                                            indent_guides=True))
                        yield Static(Syntax(javascript.create_javascript_example_for_method(endpoint, self.method),
                                            "javascript",
                                            line_numbers=True,
                                            indent_guides=True))
                        yield Static(Syntax(curl.create_curl_example_for_method(endpoint, self.method),
                                            "bash",
                                            line_numbers=True,
                                            indent_guides=True))


class EndpointsBrowser(App):
    """Textual code browser app."""

    TITLE = "Nasse"
    CSS_PATH = "browser.css"

    show_tree = var(True)

    def __init__(self, endpoints: typing.List[Endpoint],
                 localization: Localization = EnglishLocalization,
                 driver_class: Type[Driver] | None = None,
                 css_path: CSSPathType | None = None,
                 watch_css: bool = False):

        super().__init__(driver_class, css_path, watch_css)
        self.endpoints = endpoints
        self._bindings = _Bindings([
            # Binding(key="t", action="toggle_dark", description="Toggles the theme"),
            ("t", "toggle_dark", localization.tui_theme),
            ("e", "toggle_endpoints", localization.tui_explorer),
            ("q", "quit", localization.tui_quit),
        ])
        self.localization = localization

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        self.set_class(show_tree, "-show-tree")

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        yield Header(show_clock=True)
        with Horizontal():
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
            with VerticalScroll():
                yield EndpointWindow(id="endpoint-view", endpoints=self.endpoints, localization=self.localization)
        yield Footer()

    def focus_on_tree(self):
        children = self.query_one("#tree-view").focusable_children
        if children:
            children[0].focus()

    def on_mount(self, event: events.Mount) -> None:
        """When mounted"""
        self.focus_on_tree()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """When a button is pressed"""
        if event.button.id == "welcome-button":
            self.show_tree = True
            self.focus_on_tree()

    def on_tree_node_selected(
            self, event: Tree.NodeSelected
    ) -> None:
        """When an element in the endpoints tree is selected"""
        event.stop()
        if not event.node.data:
            return
        # yay
        endpoint_view = self.query_one("#endpoint-view", EndpointWindow)
        endpoint_view.focus()
        endpoint_view.scroll_home(animate=False)
        endpoint_view.load_endpoint(event.node.data)
        self.sub_title = str(event.node.label)

    def action_toggle_endpoints(self) -> None:
        """Called in response to key binding."""
        self.show_tree = not self.show_tree


if __name__ == "__main__":
    EndpointsBrowser([Endpoint(
        name="Test",
        category="Hello",
        parameters=[UserSent("param_test1", "This is a test"), UserSent("param_test2", "This is a test", required=False), ],
        headers=[UserSent("header_test1", "This is a test")],
        # sub_category="Hi"
    ),
        Endpoint(
        name="Test2",
        path="/hi",
        category="Hello",
        parameters=[UserSent("param_test2", "This is a test"), UserSent("param_test2", "This is a test", required=False), ],
        headers=[UserSent("header_test2", "This is a test")],
        # sub_category="Hi"
    )], localization=JapaneseLocalization).run()
