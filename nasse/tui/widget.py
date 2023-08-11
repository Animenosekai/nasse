"""Redefines the base widget"""
from textual.app import Widget as TextualWidget


class Widget(TextualWidget):
    """Controlling Textual widgets general behaviors"""
    _id = None
    _name = ""