"""The Nasse Endpoints Browser TUI"""

import sys
import typing
from typing import Type
from rich.console import RenderableType

from rich.syntax import Syntax
from rich.traceback import Traceback
from textual import events
from textual._path import CSSPathType
from textual.app import App, ComposeResult, CSSPathType
from textual.containers import Container, VerticalScroll
from textual.driver import Driver
from textual.reactive import var, reactive, Reactive
from textual.widgets import (Button, Checkbox, DirectoryTree, Footer, Header,
                             Input, LoadingIndicator, Placeholder, Pretty,
                             Select, Sparkline, Static, TabbedContent, Tabs,
                             Tree, Label)
from textual.widget import Widget

from nasse import Endpoint


class EndpointWindow(Widget):
    """An endpoint details window"""

    # endpoint: reactive[Endpoint] = reactive(None)

    def compose_endpoint(self, endpoint: Endpoint):
        """Creates the details view"""
        yield Label(endpoint.name)
        yield Label(endpoint.category)
        yield Button(endpoint.category, id="test1")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "test1":
            self.load_endpoint()

    def load_endpoint(self, endpoint: typing.Optional[Endpoint] = None):
        """Loads the given endpoint"""

        # Cleaning up
        self.remove_children()

        if not endpoint:
            return self.mount(Button("Start by selecting an endpoint", id="welcome-button"))

        # Mounting the endpoint view
        self.mount_all(self.compose_endpoint(endpoint))

    def compose(self) -> ComposeResult:
        yield Button("Start by selecting an endpoint", id="welcome-button")


class EndpointsBrowser(App):
    """Textual code browser app."""

    TITLE = "Nasse"
    CSS_PATH = "browser.css"
    BINDINGS = [
        ("t", "toggle_dark", "Theme"),
        ("e", "toggle_endpoints", "Endpoints Explorer"),
        ("q", "quit", "Quit"),
    ]

    show_tree = var(True)

    def __init__(self, endpoints: typing.List[Endpoint], driver_class: Type[Driver] | None = None, css_path: CSSPathType | None = None, watch_css: bool = False):
        super().__init__(driver_class, css_path, watch_css)

        self.endpoints = endpoints

    @property
    def categories(self) -> typing.Dict[str, typing.Dict[str, typing.List[Endpoint]]]:
        """Returns the category separated endpoints"""
        mid_results: typing.Dict[str, typing.List[Endpoint]] = {}
        for endpoint in self.endpoints:
            try:
                mid_results[endpoint.category].append(endpoint)
            except Exception:
                mid_results[endpoint.category] = [endpoint]

        results = {}
        for category, endpoints in mid_results.items():
            results[category] = {}
            for endpoint in endpoints:
                try:
                    results[category][endpoint.sub_category or "@TopLevelEndpoint"].append(endpoint)
                except Exception:
                    results[category][endpoint.sub_category or "@TopLevelEndpoint"] = [endpoint]
        return results

    def watch_show_tree(self, show_tree: bool) -> None:
        """Called when show_tree is modified."""
        self.set_class(show_tree, "-show-tree")

    def compose(self) -> ComposeResult:
        """Compose our UI."""
        yield Header(show_clock=True)
        with Container():
            with Container(id="tree-view"):
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
                yield EndpointWindow(id="endpoint-view")
        yield Footer()

    # def on_mount(self, event: events.Mount) -> None:
    #     self.query_one("#tree-view").focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "welcome-button":
            self.show_tree = True
            self.query_one("#tree-view").focus()

    def on_tree_node_selected(
            self, event: Tree.NodeSelected
    ) -> None:
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
        # sub_category="Hi"
    )]).run()
