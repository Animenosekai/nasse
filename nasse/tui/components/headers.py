"""Defines custom headers"""
from textual.widgets import Label

from nasse.tui.widget import Widget


class StickyHeader(Widget):
    """A sticky header"""
    DEFAULT_CSS = """
    StickyHeader {
        align: center top;
        dock: top;
        padding: 1;
        height: auto;
    }
    """

    def __init__(self, title: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.title = title

    def compose(self):
        yield Label(f"[underline][bold]{self.title}[/bold][/underline]")
        # yield SectionTitle(self.title)
