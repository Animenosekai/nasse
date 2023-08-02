from parser import Path, resolve


AVAILABLE_PATHS = [
    Path("/"),
    Path("/hello"),
    Path("/hello/world"),
    Path("/pages"),
    Path("/pages/1"),
    Path("/pages/<int:page>"),
    Path("/yay/<name>")
]
