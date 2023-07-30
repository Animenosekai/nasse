"""
Helper to create static Python code from Nasse objects
"""

import pathlib
import json
from nasse.models import Endpoint, Error, Login, Return, UserSent
# from nasse.utils.logging import logger


def return_to_python(element: Return,
                     indent: str = " " * 4,
                     end_indent: str = "") -> str:
    """Turns the given `Return` object to a static python snippet of code"""
    result = "Return(\n"
    result += indent + "name=" + \
        json.dumps(element.name, ensure_ascii=False) + ",\n"
    if element.example:
        result += indent + "example=" + (json.dumps(element.example, ensure_ascii=False)
                                           if isinstance(element.example, str)
                                           else str(element.example)) + ",\n"
    if element.description:
        result += indent + "description=" + \
            json.dumps(element.description, ensure_ascii=False) + ",\n"
    if element.type:
        result += indent + "type=" + \
            json.dumps(str(element.type), ensure_ascii=False) + ",\n"
    if element.children:
        result += indent + "children=" + str(element.children) + ",\n"
    result += indent + "nullable = " + str(element.nullable) + "\n"
    result += end_indent + ")"
    return result


def login_to_python(element: Login,
                    indent: str = " " * 4,
                    end_indent: str = "") -> str:
    """Turns the given `Login` object to a static python snippet of code"""
    result = "Login(\n"
    if element.required:
        result += indent + "required=True,\n"
    if element.types:
        # we can't really convert non-str types
        result += indent + "types=" + str(element.types) + ",\n"
    if element.skip:
        result += indent + "skip=True,\n"
    if element.skip_fetch:
        result += indent + "skip_fetch=True\n"

    result += end_indent + ")"
    return result


def usersent_to_python(element: UserSent,
                       indent: str = " " * 4,
                       end_indent: str = "") -> str:
    """Turns the given `UserSent` object to a static python snippet of code"""
    result = "{t}(\n".format(t=element.__class__.__name__)
    result += indent + "name=" + \
        json.dumps(element.name, ensure_ascii=False) + ",\n"

    if element.description:
        result += indent + "description=" + \
            json.dumps(element.description, ensure_ascii=False) + ",\n"
    if not element.required:
        result += indent + "required=False,\n"

    if element.type != str:
        has_name = (hasattr(element, '__name__') and not isinstance(element, str))
        result += indent + f"type={element.type.__name__ if has_name else str(element.type)}"

    # we can't convert types for now
    # logger.warn("It is not possible to convert types to static python code for now")

    result += end_indent + ")"
    return result


def error_to_python(element: Error,
                    indent: str = " " * 4,
                    end_indent: str = "") -> str:
    """Turns the given `Error` object to a static python snippet of code"""
    result = "Error(\n"
    result += indent + "name=" + \
        json.dumps(element.name, ensure_ascii=False) + ",\n"

    if element.description:
        result += indent + "description=" + \
            json.dumps(element.description, ensure_ascii=False) + ",\n"

    if element.code != 500:
        result += indent + "code=" + str(element.code) + ",\n"

    result += end_indent + ")"
    return result


def endpoint_to_python(endpoint: Endpoint, explicit_path: bool = True, indent: str = " " * 4) -> str:
    """Turns the given `Endpoint` object to a static python snippet of code"""
    result = "Endpoint(\n"

    if explicit_path:
        result += indent + "path=" + \
            json.dumps(endpoint.path, ensure_ascii=False) + ",\n"

    if not len(endpoint.methods) == 1 or list(endpoint.methods)[0] != "GET":
        result += indent + "methods=" + str(endpoint.methods) + ",\n"

    if not endpoint.json:
        result += indent + "json=False"

    for attribute in ("name", "category", "sub_category", "description", "base_dir"):
        element = getattr(endpoint, attribute)
        if isinstance(element, pathlib.Path):
            element = str(element)
        if isinstance(element, set):
            element = list(element)
        result += indent + f"{attribute}=" + \
            json.dumps(element, ensure_ascii=False) + ",\n"

    for attribute, caster in [("headers", usersent_to_python),
                              ("cookies", usersent_to_python),
                              ("parameters", usersent_to_python),
                              ("dynamics", usersent_to_python),
                              ("returns", return_to_python),
                              ("login", login_to_python),
                              ("errors", error_to_python)]:
        element = getattr(endpoint, attribute)
        if not element or (len(element) == 1 and
                           "*" in element and
                           not element.get("*", set())):
            continue

        result += indent + attribute + "={\n"
        for method, values in element.items():
            if not values:
                continue
            result += indent * 2 + f'"{method}": [\n'
            for element in values:
                result += indent * 3 + \
                    caster(element, indent=indent * 4,
                           end_indent=indent * 3) + ",\n"
            result += indent * 2 + "],\n"
        result += indent + "},\n"

    result += ")"
    return result


def endpoint_to_decorator(endpoint: Endpoint, app_name: str = "app", explicit_path: bool = True, indent: str = " " * 4):
    """Turns the given `Endpoint` object to a static python snippet of code with a decorator"""
    return "@{name}.route(endpoint={result})".format(name=app_name,
                                            result=endpoint_to_python(endpoint=endpoint, explicit_path=explicit_path, indent=indent))
