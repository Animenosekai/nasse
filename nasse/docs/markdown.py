"""
Automatically generates Markdown Docs

Copyright
---------
Animenosekai
    Original author, MIT License
"""

# pylint: disable=consider-using-f-string

import typing
import inspect
import os.path
import urllib.parse
import pathlib

from nasse import docs, models
from nasse.docs.header import header_link
from nasse.localization.base import Localization
from nasse.utils.sanitize import sort_http_methods


def make_docs(endpoint: models.Endpoint,
              postman: bool = False,
              curl: bool = True,
              javascript: bool = True,
              python: bool = True,
              localization: Localization = Localization(),
              base_dir: typing.Optional[pathlib.Path] = None) -> str:
    """
    Generates the documentation for the given endpoint

    Parameters
    ----------
    endpoint: models.Endpoint
        The endpoint to generate the docs for
    postman: bool, default = False
        If the docs are generated for Postman
        (doesn't include all of the details since a lot is already included by the Postamn docs generator)
    curl: bool, default = True
        If the `curl` examples should be included too
    javascript: bool, default = True
        If the JavaScript examples should be included too
    python: bool, default = True
        If the Python examples should be included too
    localization: Localization, optional
        The language to use to create the docs

    Returns
    -------
    str
        The generated docs
    """

    result = """
# {name}
""".format(name=endpoint.name)

    kwargs = {"endpoint": endpoint,
              "postman": postman,
              "curl": curl,
              "javascript": javascript,
              "python": python,
              "localization": localization,
              "base_dir": base_dir}

    if len(endpoint.methods) <= 1:
        result += """
{}
""".format(endpoint.description.get(list(endpoint.methods)[0], endpoint.description.get("*", localization.no_description)))
        result += make_docs_for_method(**kwargs)
    else:
        for method in sort_http_methods(endpoint.methods):
            kwargs["method"] = method
            result += "\n - ### {}".format(localization.using_method.format(method=method))
            result += "\n{}\n".format(make_docs_for_method(**kwargs))
    return result


def make_docs_for_method(
        endpoint: models.Endpoint,
        method: typing.Optional[str] = None,
        postman: bool = False,
        curl: bool = True,
        javascript: bool = True,
        python: bool = True,
        localization: Localization = Localization(),
        base_dir: typing.Optional[pathlib.Path] = None) -> str:
    """
    Creates the docs for the given method

    Parameters
    ----------
    endpoint: models.Endpoint
        The endpoint to generate the docs for
    method: str, optional
        The method to generate the docs for
    postman: bool, default = False
        If the docs are generated for Postman
        (doesn't include all of the details since a lot is already included by the Postamn docs generator)
    curl: bool, default = True
        If the `curl` examples should be included too
    javascript: bool, default = True
        If the JavaScript examples should be included too
    python: bool, default = True
        If the Python examples should be included too
    localization: Localization, optional
        The language to use to create the docs

    Returns
    -------
    str
        The generated docs
    """
    result = ""

    if len(endpoint.methods) == 1 or method is None:
        # treating it as only a single method endpoint
        heading_level = "###"
        method = list(endpoint.methods)[0]
    else:
        heading_level = "####"
        method = str(method)
        result += """
{}
""".format(endpoint.description.get(method if method in endpoint.description else "*",
                                    localization.no_description))

    try:
        unwrapped = inspect.unwrap(endpoint.handler)
        source_file = inspect.getsourcefile(unwrapped)
    except Exception:
        source_file = endpoint.handler.__code__.co_filename

    try:
        base = pathlib.Path(base_dir or pathlib.Path() / "docs").absolute()
        source_file = pathlib.Path(source_file).absolute()
        common = pathlib.Path(os.path.commonpath([str(source_file), str(base)])).resolve()
        # Getting the relative path
        path = pathlib.Path(source_file).resolve().relative_to(common)
        # Distance between the docs and the most deep common path
        distance = str(base).count("/") - str(common).count("/") + 1
        path = pathlib.Path("../" * distance + str(path))
    except Exception:
        path = pathlib.Path(source_file)

    line = endpoint.handler.__code__.co_firstlineno

    # ENDPOINT HEADING

    if not postman:
        result += """
```http
{method} {path}
```

> [{source_code_path}]({github_path})
""".format(method=method,
           path=endpoint.path,
           source_code_path=path,
           # FIXME: this needs to be fixed because it fails sometimes
           github_path="{path}#L{line}".format(path=path.as_posix(), line=line))

    else:
        result = """
> [{source_code_path}]({github_path})

{description}

""".format(source_code_path=path,
            github_path="../../{path}#L{line}".format(path=path, line=line),
            description=endpoint.description.get(method if method in endpoint.description else "*",
                                                 localization.no_description))


# AUTHENTICATION

    result += """
{heading} {localization__authentication}

""".format(heading=heading_level, localization__authentication=localization.authentication)

    rules = endpoint.login.get(method, endpoint.login["*"])
    if not rules:
        result += localization.no_auth_rule
    else:
        for login_rule in rules:
            if login_rule.skip:
                result += localization.no_login
            else:
                if login_rule.required:
                    if len(login_rule.types) > 0:
                        result += localization.login_with_types_required.format(types=', '.join(str(type_name) for type_name in login_rule.types))
                    else:
                        result += localization.login_required
                else:
                    if len(login_rule.types) > 0:
                        result += localization.login_with_types_optional.format(types=', '.join(str(type_name) for type_name in login_rule.types))
                    else:
                        result += localization.login_optional

            if login_rule.skip_fetch:
                result += localization.login_suffix_only_verified

    if not postman:  # POSTMAN DOESN'T NEED THESE INFORMATION

        # USER SENT VALUES

        for field, values in [
            (localization.dynamic_url, endpoint.dynamics),
            (localization.parameters, endpoint.params),
            (localization.headers, endpoint.headers),
            (localization.cookies, endpoint.cookies)
        ]:
            params = models.get_method_variant(method, values)
            if len(params) > 0:
                result += """

{heading} {field}

| {localization__name}         | {localization__description}                      | {localization__required}         | {localization__type}             |
| ------------ | -------------------------------- | ---------------- | ---------------- |
""".format(field=field,
                    heading=heading_level,
                    localization__name=localization.name,
                    localization__description=localization.description,
                    localization__required=localization.required,
                    localization__type=localization.type)
                result += "\n".join(
                    ["| `{param}` | {description}  | {required}            | {type}            |".format(param=param.name,
                                                                                                         description=param.description or localization.no_description,
                                                                                                         required=localization.yes if param.required else localization.no,
                                                                                                         type=param.type.__name__ if hasattr(param.type, "__name__") else str(param.type) if param.type is not None else "str") for param in params])


# LANGUAGE SPECIFIC EXAMPLES

        if any((curl, javascript, python)):
            result += """

{heading} {localization__example}

<!-- tabs:start -->
""".format(heading=heading_level, localization__example=localization.example)
            for proceed, highlight, language, function in [
                (curl, "bash", "cURL", docs.curl.create_curl_example_for_method),
                (javascript, "javascript", "JavaScript", docs.javascript.create_javascript_example_for_method),
                (python, "python", "Python", docs.python.create_python_example_for_method)
            ]:
                if proceed:
                    result += """

<details>
    <summary>{language} {localization__example}</summary>

{heading} **{language}**

```{highlight}
{example}
```

</details>
""".format(heading=heading_level + "#",
                        localization__example=localization.example,
                        highlight=highlight,
                        language=language,
                        example=function(endpoint, method=method))
            result += """<!-- tabs:end -->"""


# RESPONSE
    returning = models.get_method_variant(method, endpoint.returns)
    if len(returning) > 0:
        result += """

{heading} {localization__response}
""".format(heading=heading_level, localization__response=localization.response)


# JSON RESPONSE EXAMPLE

        if endpoint.json:
            result += """
{heading} {localization__example_response}

```json
{example}
```
""".format(heading=heading_level + "#",
                localization__example_response=localization.example_response,
                example=docs.example.generate_example(endpoint, method=method))
        else:
            result += "\n"
            result += localization.not_json_response
            result += "\n"

# RESPONSE DESCRIPTION

        result += """
{heading} {localization__returns}

| {localization__field}        | {localization__description}                      | {localization__type}   | {localization__nullable}  |
| ----------   | -------------------------------- | ------ | --------- |
""".format(heading=heading_level + "#",
           localization__returns=localization.returns,
           localization__field=localization.field,
           localization__description=localization.description,
           localization__type=localization.type,
           localization__nullable=localization.nullable)

        result += "\n".join(["| `{key}` | {description}  | {type}      | {nullable}      |".format(key=element.name,
                                                                                                   description=element.description or localization.no_description,
                                                                                                   type=docs.example._get_type(element),
                                                                                                   nullable=localization.yes if element.nullable else localization.no)
                             for element in returning])

    result += "\n"


# ERRORS

    errors = models.get_method_variant(method, endpoint.errors)
    if len(errors) > 0:
        result += """
{heading} {localization__possible_errors}

| {localization__exception}         | {localization__description}                      | {localization__code}   |
| ---------------   | -------------------------------- | ------ |
""".format(heading=heading_level + "#",
           localization__possible_errors=localization.possible_errors,
           localization__exception=localization.exception,
           localization__description=localization.description,
           localization__code=localization.code)

        result += "\n".join(["| `{key}` | {description}  | {code}  |".format(key=error.name,
                                                                             description=error.description or localization.no_description,
                                                                             code=error.code)
                             for error in errors])


# INDEX LINKING

    result += "\n[{localization__return_to_index}](../{localization__getting_started}.md#{localization__index})".format(
        localization__return_to_index=localization.return_to_index,
        localization__getting_started=urllib.parse.quote(localization.getting_started, safe=""),
        localization__index=header_link(localization.index))
    return result
