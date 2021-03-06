import urllib.parse
from pathlib import Path

from nasse import docs, models
from nasse.docs.header import header_link
from nasse.docs.localization.base import Localization
from nasse.utils.sanitize import sort_http_methods


def make_docs(endpoint: models.Endpoint, postman: bool = False, curl: bool = True, javascript: bool = True, python: bool = True, localization: Localization = Localization()):
    result = '''
# {name}
'''.format(name=endpoint.name)
    if len(endpoint.methods) == 1:
        result += '''
{description}
'''.format(description=endpoint.description.get(endpoint.methods[0] if "*" not in endpoint.description else "*", localization.no_description))
        result += make_docs_for_method(endpoint=endpoint, postman=postman, curl=curl, javascript=javascript, python=python, localization=localization)
    else:
        for method in sort_http_methods(endpoint.methods):
            result += "\n - ### {localization__using_method}".format(localization__using_method=localization.using_method.format(method=method))
            result += "\n{docs}\n".format(docs=make_docs_for_method(endpoint=endpoint, method=method,
                                          postman=postman, curl=curl, javascript=javascript, python=python, localization=localization))
    return result


def make_docs_for_method(endpoint: models.Endpoint, method: str = None, postman: bool = False, curl: bool = True, javascript: bool = True, python: bool = True, localization: Localization = Localization()):
    result = ''

# ENDPOINT HEADER

    if len(endpoint.methods) == 1 or method is None:
        heading_level = "###"
        method = list(endpoint.methods)[0]
    else:
        heading_level = "####"
        method = str(method)
        result += '''
{description}
'''.format(description=endpoint.description.get(method if method in endpoint.description else "*", localization.no_description))

    try:
        path = Path(endpoint.handler.__code__.co_filename).resolve().relative_to(Path().resolve())
    except Exception:
        path = Path(endpoint.handler.__code__.co_filename)
    line = endpoint.handler.__code__.co_firstlineno


# ENDPOINT HEADING

    if not postman:
        result += '''
```http
{method} {path}
```

> [{source_code_path}]({github_path})
'''.format(method=method, path=endpoint.path, source_code_path=path, github_path="../../{path}#L{line}".format(path=path, line=line))

    else:
        result = '''
> [{source_code_path}]({github_path})

{description}

'''.format(source_code_path=path, github_path="../../{path}#L{line}".format(path=path, line=line), description=endpoint.description.get(method if method in endpoint.description else "*", localization.no_description))


# AUTHENTICATION

    result += '''
{heading} {localization__authentication}

'''.format(heading=heading_level, localization__authentication=localization.authentication)
    login_rules = endpoint.login.get(method, endpoint.login.get("*", None))
    if login_rules is None:
        result += localization.no_auth_rule
    else:
        if login_rules.no_login:
            result += localization.no_login
        else:
            if login_rules.required:
                if len(login_rules.types) > 0:
                    result += localization.login_with_types_required.format(types=', '.join(str(type_name) for type_name in login_rules.types))
                else:
                    result += localization.login_required
            else:
                if len(login_rules.types) > 0:
                    result += localization.login_with_types_optional.format(types=', '.join(str(type_name) for type_name in login_rules.types))
                else:
                    result += localization.login_optional

        if login_rules.verification_only:
            result += localization.login_suffix_only_verified

    if not postman:  # POSTMAN DOESN'T NEED THESE INFORMATION

        # USER SENT VALUES

        for field, values in [
            (localization.parameters, endpoint.params),
            (localization.headers, endpoint.headers),
            (localization.cookies, endpoint.cookies),
            (localization.dynamic_url, endpoint.dynamics)
        ]:
            params = [param for param in values if (param.all_methods or method in param.methods)]
            if len(params) > 0:
                result += '''

{heading} {field}

| {localization__name}         | {localization__description}                      | {localization__required}         | {localization__type}             |
| ------------ | -------------------------------- | ---------------- | ---------------- |
'''.format(field=field, heading=heading_level, localization__name=localization.name, localization__description=localization.description, localization__required=localization.required, localization__type=localization.type)
                result += "\n".join(
                    ["| `{param}` | {description}  | {required}            | {type}            |".format(param=param.name, description=param.description, required=localization.yes if param.required else localization.no, type=param.type.__name__ if hasattr(param.type, "__name__") else str(param.type) if param.type is not None else "str") for param in params])


# LANGUAGE SPECIFIC EXAMPLES

        if any((curl, javascript, python)):
            result += '''

{heading} {localization__example}

<!-- tabs:start -->
'''.format(heading=heading_level, localization__example=localization.example)
            for proceed, highlight, language, function in [
                (curl, "bash", "cURL", docs.curl.create_curl_example_for_method),
                (javascript, "javascript", "JavaScript", docs.javascript.create_javascript_example_for_method),
                (python, "python", "Python", docs.python.create_python_example_for_method)
            ]:
                if proceed:
                    result += '''

<details>
    <summary>{language} {localization__example}</summary>

{heading} **{language}**

```{highlight}
{example}
```

</details>
'''.format(heading=heading_level + "#", localization__example=localization.example, highlight=highlight, language=language, example=function(endpoint, method=method))
            result += '''<!-- tabs:end -->'''


# RESPONSE

    returning = [element for element in endpoint.returning if (element.all_methods or method in element.methods)]
    if len(returning) > 0:
        result += '''

{heading} {localization__response}
'''.format(heading=heading_level, localization__response=localization.response)


# JSON RESPONSE EXAMPLE

        if endpoint.json:
            result += '''
{heading} {localization__example_response}

```json
{example}
```
'''.format(heading=heading_level + "#", localization__example_response=localization.example_response, example=docs.example.generate_example(endpoint, method=method))
        else:
            result += "\n"
            result += localization.not_json_response
            result += "\n"

# RESPONSE DESCRIPTION

        result += '''
{heading} {localization__returns}

| {localization__field}        | {localization__description}                      | {localization__type}   | {localization__nullable}  |
| ----------   | -------------------------------- | ------ | --------- |
'''.format(heading=heading_level + "#", localization__returns=localization.returns, localization__field=localization.field, localization__description=localization.description, localization__type=localization.type, localization__nullable=localization.nullable)
        result += "\n".join(["| `{key}` | {description}  | {type}      | {nullable}      |".format(key=element.name,
                            description=element.description, type=docs.example._get_type(element), nullable=localization.yes if element.nullable else localization.no) for element in returning])

    result += "\n"


# ERRORS

    errors = [error for error in endpoint.errors if (
        error.all_methods or method in error.methods)]
    if len(errors) > 0:
        result += '''
{heading} {localization__possible_errors}

| {localization__exception}         | {localization__description}                      | {localization__code}   |
| ---------------   | -------------------------------- | ------ |
'''.format(heading=heading_level + "#", localization__possible_errors=localization.possible_errors, localization__exception=localization.exception, localization__description=localization.description, localization__code=localization.code)

        result += "\n".join(
            ["| `{key}` | {description}  | {code}  |".format(key=error.name, description=error.description, code=error.code) for error in errors])


# INDEX LINKING

    result += "\n[{localization__return_to_index}](../{localization__getting_started}.md#{localization__index})".format(
        localization__return_to_index=localization.return_to_index,
        localization__getting_started=urllib.parse.quote(localization.getting_started, safe=""),
        localization__index=header_link(localization.index))
    return result
