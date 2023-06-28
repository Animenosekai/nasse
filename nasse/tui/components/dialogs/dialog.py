"""
(original file: https://github.com/Textualize/frogmouth/blob/main/frogmouth/dialogs/text_dialog.py)
Provides a base modal dialog for showing text to the user.

Copyright
---------
Dave Pearson (davep)
    Original Author; https://github.com/davep
Will McGugan (willmcgugan)
    Original Author; https://github.com/willmcgugan

License
-------
MIT License

Copyright (c) 2023 Textualize, Inc

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""

from rich.text import TextType
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static
from textual.widgets._button import ButtonVariant


class TextDialog(ModalScreen[None]):
    """Base modal dialog for showing information."""

    DEFAULT_CSS = """
    TextDialog {
        align: center middle;
    }

    TextDialog Center {
        width: 100%;
    }

    TextDialog > Vertical {
        background: $boost;
        min-width: 30%;
        width: auto;
        height: auto;
        border: round $primary;
    }

    TextDialog Static {
        width: auto;
    }

    TextDialog .spaced {
        padding: 1 4;
    }

    TextDialog #message {
        min-width: 100%;
    }
    """
    """Default CSS for the base text modal dialog."""

    BINDINGS = [
        Binding("escape", "dismiss(None)", "", show=False),
    ]
    """Bindings for the base text modal dialog."""

    def __init__(self, title: TextType, message: TextType) -> None:
        """Initialise the dialog.

        Args:
            title: The title for the dialog.
            message: The message to show.
        """
        super().__init__()
        self._title = title
        self._message = message

    @property
    def button_style(self) -> ButtonVariant:
        """The style for the dialog's button."""
        return "primary"

    def compose(self) -> ComposeResult:
        """Compose the content of the modal dialog."""
        with Vertical():
            with Center():
                yield Static(self._title, classes="spaced")
            yield Static(self._message, id="message", classes="spaced")
            with Center(classes="spaced"):
                yield Button("OK", variant=self.button_style)

    def on_mount(self) -> None:
        """Configure the dialog once the DOM has loaded."""
        self.query_one(Button).focus()

    def on_button_pressed(self) -> None:
        """Handle the OK button being pressed."""
        self.dismiss(None)
