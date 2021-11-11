"""
Helper to create static Python code from Nasse objects
"""
import json
from nasse.models import Endpoint, Error, Login, Return, UserSent


def return_to_python(element: Return, indent: str = " " * 4, end_indent: str = ""):
    result = "Return(\n"
    result += indent + "name = " + \
        json.dumps(element.name, ensure_ascii=False) + ",\n"
    if element.example:
        result += indent + "example = " + (json.dumps(element.example, ensure_ascii=False) if isinstance(
            element.example, str) else str(element.example)) + ",\n"
    if element.description:
        result += indent + "description = " + \
            json.dumps(element.description, ensure_ascii=False) + ",\n"
    if element.type:
        result += indent + "type = " + \
            json.dumps(str(element.type), ensure_ascii=False) + ",\n"
    if element.children:
        result += indent + "children = " + str(element.children) + ",\n"
    result += indent + "methods = " + str(element.methods) + ",\n"
    result += indent + "nullable = " + str(element.nullable) + "\n"
    result += end_indent + ")"
    return result


def login_to_python(element: Login, indent: str = " " * 4, end_indent: str = ""):
    result = "Login(\n"
    if element.required:
        result += indent + "required = True,\n"
    if element.types:
        # we can't really convert non-str types
        result += indent + "types = " + str(element.types) + ",\n"
    result += indent + "methods = " + str(element.methods) + ",\n"
    if element.no_login:
        result += indent + "no_login = True,\n"
    if element.verification_only:
        result += indent + "verification_only = True\n"

    result += end_indent + ")"
    return result


def usersent_to_python(element: UserSent, indent: str = " " * 4, end_indent: str = ""):
    result = "{t}(\n".format(t=element.__class__.__name__)
    result += indent + "name = " + \
        json.dumps(element.name, ensure_ascii=False) + ",\n"

    if element.description:
        result += indent + "description = " + \
            json.dumps(element.description, ensure_ascii=False) + ",\n"
    if not element.required:
        result += indent + "required = False,\n"
    result += indent + "methods = " + str(element.methods) + "\n"

    # we can't convert types for now

    result += end_indent + ")"
    return result


def error_to_python(element: Error, indent: str = " " * 4, end_indent: str = ""):
    result = "Error(\n"
    result += indent + "name = " + \
        json.dumps(element.name, ensure_ascii=False) + ",\n"

    if element.description:
        result += indent + "description = " + \
            json.dumps(element.description, ensure_ascii=False) + ",\n"

    if element.code != 500:
        result += indent + "code = " + str(element.code) + ",\n"
    result += indent + "methods = " + str(element.methods) + "\n"

    result += end_indent + ")"
    return result


def endpoint_to_python(endpoint: Endpoint, explicit_path: bool = True, indent: str = " " * 4):
    result = "Endpoint(\n"

    if explicit_path:
        result += indent + "path = " + \
            json.dumps(endpoint.path, ensure_ascii=False) + ",\n"

    if not len(endpoint.methods) == 1 or list(endpoint.methods)[0] != "GET":
        result += indent + "methods = " + str(endpoint.methods) + ",\n"

    if not endpoint.json:
        result += indent + "json = False"

    result += indent + "name = " + \
        json.dumps(endpoint.name, ensure_ascii=False) + ",\n"

    result += indent + "description = " + \
        json.dumps(endpoint.description, ensure_ascii=False) + ",\n"

    if endpoint.section != "Other":
        result += indent + "section = " + \
            json.dumps(endpoint.section, ensure_ascii=False) + ",\n"

    if endpoint.returning:
        result += indent + "returning = [\n"
        for elem in endpoint.returning:
            result += indent * 2 + \
                return_to_python(elem, indent=indent * 3,
                                 end_indent=indent * 2) + ",\n"
        result += indent + "],\n"

    result += indent + "login = " + \
        login_to_python(endpoint.login, indent=indent *
                        2, end_indent=indent) + ",\n"

    if endpoint.headers:
        result += indent + "headers = [\n"
        for elem in endpoint.headers:
            result += indent * 2 + \
                usersent_to_python(elem, indent=indent * 3,
                                   end_indent=indent * 2) + ",\n"
        result += indent + "],\n"

    if endpoint.cookies:
        result += indent + "cookies = [\n"
        for elem in endpoint.cookies:
            result += indent * 2 + \
                usersent_to_python(elem, indent=indent * 3,
                                   end_indent=indent * 2) + ",\n"
        result += indent + "],\n"

    if endpoint.params:
        result += indent + "params = [\n"
        for elem in endpoint.params:
            result += indent * 2 + \
                usersent_to_python(elem, indent=indent * 3,
                                   end_indent=indent * 2) + ",\n"
        result += indent + "],\n"

    if endpoint.errors:
        result += indent + "errors = [\n"
        for elem in endpoint.errors:
            result += indent * 2 + \
                error_to_python(elem, indent=indent * 3,
                                end_indent=indent * 2) + ",\n"
        result += indent + "],\n"

    result += ")"
    return result


def endpoint_to_decorator(endpoint: Endpoint, app_name: str = "app", explicit_path: bool = True, indent: str = " " * 4):
    return "@{name}.route({result})".format(name=app_name, result=endpoint_to_python(endpoint=endpoint, explicit_path=explicit_path, indent=indent))
