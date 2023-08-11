import re
PATH_PARTS_REGEX = re.compile(r"""(?<dynamic>((?<=(__))[\S]+(?=(__))))|(?<part>[^_]+)""")

def to_path(name: str) -> str:
    matches = PATH_PARTS_REGEX.search(str(name))
    if not matches:
        return "/"
    for element in matches.groupdict():
        element
