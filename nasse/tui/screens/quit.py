"""The quitting screen"""

from textual.containers import Grid
from textual.screen import ModalScreen
from textual.widgets import Button, Label
from textual import events
import typing
from nasse.localization import Localization, EnglishLocalization


class QuitScreen(ModalScreen):
    """Screen with a dialog to quit."""

    DEFAULT_CSS = """
    QuitScreen {
        align: center middle;
    }

    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }

    #question {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }

    Button {
        width: 100%;
    }
    """

    def __init__(self, localization: typing.Type[Localization] = EnglishLocalization, **kwargs) -> None:
        super().__init__(**kwargs)
        self.localization = localization

    def compose(self):
        yield Grid(
            Label(self.localization.tui_quit_confirmation, id="question"),
            Button(self.localization.tui_quit, variant="error", id="quit"),
            Button(self.localization.tui_cancel, variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """When a button is pressed"""
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()

    def on_key(self, event: events.Key) -> None:
        """When a key is pressed on the keyboard"""
        if event.key == "escape":
            self.app.pop_screen()
