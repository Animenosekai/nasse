from textual import events, keys
from textual.widgets import Input as DefaultInput


class Input(DefaultInput):
    """A (custom) text input widget."""

    def on_key(self, event: events.Key) -> None:
        """Checks for `enter` or `esc` to blur the input"""
        if event.key in (keys.Keys.Enter, keys.Keys.Escape):
            try:
                self.screen.set_focus(None)
            except Exception:
                self.blur()
