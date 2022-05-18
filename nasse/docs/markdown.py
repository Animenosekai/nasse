from pathlib import Path

from nasse import docs, models
from nasse.utils.sanitize import sort_http_methods


def make_docs(endpoint: models.Endpoint, postman: bool = False, curl: bool = True, javascript: bool = True, python: bool = True):
    result = '''
## {name}
'''.format(name=endpoint.name)
    if len(endpoint.methods) == 1:
        result += '''
{description}
'''.format(description=endpoint.description.get(endpoint.methods[0] if "*" not in endpoint.description else "*", 'No description'))
        result += make_docs_for_method(endpoint=endpoint)
    else:
        for method in sort_http_methods(endpoint.methods):
            result += '''\n- ### Using {method}\n{docs}\n'''.format(method=method, docs=make_docs_for_method(
                endpoint=endpoint, method=method, postman=postman, curl=curl, javascript=javascript, python=python))
    return result


def make_docs_for_method(endpoint: models.Endpoint, method: str = None, postman: bool = False, curl: bool = True, javascript: bool = True, python: bool = True):
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
'''.format(description=endpoint.description.get(method if method in endpoint.description else "*", 'No description'))

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

'''.format(source_code_path=path, github_path="../../{path}#L{line}".format(path=path, line=line), description=endpoint.description.get(method if method in endpoint.description else "*", 'No description'))


# AUTHENTICATION

    result += '''
{heading} Authentication

'''.format(heading=heading_level)
    login_rules = endpoint.login.get(method, endpoint.login.get("*", None))
    if login_rules is None:
        result += "There is no authentication rules defined"
    else:
        if login_rules.no_login:
            result += "Login is **not** required"
        else:
            if login_rules.required:
                result += "Login{types} is **required**".format(types=(' with ' + ', '.join(
                    [str(type_name) for type_name in login_rules.types])) if len(login_rules.types) > 0 else "")
            else:
                result += "Login{types} is **optional**".format(types=(' with ' + ', '.join(
                    [str(type_name) for type_name in login_rules.types])) if len(login_rules.types) > 0 else "")

        if login_rules.verification_only:
            result += " but only verified"

    if not postman:  # POSTMAN DOESN'T NEED THESE INFORMATION

        # USER SENT VALUES

        for field, values in [
            ("Parameters", endpoint.params),
            ("Headers", endpoint.headers),
            ("Cookies", endpoint.cookies),
            ("Dynamic URL", endpoint.dynamics)
        ]:
            params = [param for param in values if (param.all_methods or method in param.methods)]
            if len(params) > 0:
                result += '''

{heading} {field}

| Name         | Description                      | Required         | Type             |
| ------------ | -------------------------------- | ---------------- | ---------------- |
'''.format(field=field, heading=heading_level)
                result += "\n".join(
                    ["| `{param}` | {description}  | {required}            | {type}            |".format(param=param.name, description=param.description, required=param.required, type=param.type.__name__ if hasattr(param.type, "__name__") else str(param.type) if param.type is not None else "str") for param in params])


# LANGUAGE SPECIFIC EXAMPLES

        if any((curl, javascript, python)):
            result += '''

{heading} Example

<!-- tabs:start -->
'''.format(heading=heading_level)
            for proceed, language, function in [
                (curl, "cURL", docs.curl.create_curl_example_for_method),
                (javascript, "JavaScript", docs.javascript.create_javascript_example_for_method),
                (python, "Python", docs.python.create_python_example_for_method)
            ]:
                if proceed:
                    result += '''
{heading} **{language}**

```bash
{example}
```
'''.format(heading=heading_level + "#", language=language, example=function(endpoint, method=method))
            result += '''<!-- tabs:end -->'''


# RESPONSE

    returning = [element for element in endpoint.returning if (element.all_methods or method in element.methods)]
    if len(returning) > 0:
        result += '''

{heading} Response
'''.format(heading=heading_level)


# JSON RESPONSE EXAMPLE

        if endpoint.json:
            result += '''
{heading} Example Response

```json
{example}
```
'''.format(heading=heading_level + "#", example=docs.example.generate_example(endpoint, method=method))
        else:
            result += '''\nThis endpoint doesn't seem to return a JSON formatted response.\n'''

# RESPONSE DESCRIPTION

        result += '''
{heading} Returns

| Field        | Description                      | Type   | Nullable  |
| ----------   | -------------------------------- | ------ | --------- |
'''.format(heading=heading_level + "#")
        result += "\n".join(["| `{key}` | {description}  | {type}      | {nullable}      |".format(key=element.name,
                            description=element.description, type=docs.example._get_type(element), nullable=element.nullable) for element in returning])

    result += "\n"


# ERRORS

    errors = [error for error in endpoint.errors if (
        error.all_methods or method in error.methods)]
    if len(errors) > 0:
        result += '''
{heading} Possible Errors

| Exception         | Description                      | Code   |
| ---------------   | -------------------------------- | ------ |
'''.format(heading=heading_level + "#")

        result += "\n".join(
            ["| `{key}` | {description}  | {code}  |".format(key=error.name, description=error.description, code=error.code) for error in errors])


# INDEX LINKING

    result += "\n[Return to the Index](../Getting%20Started.md#index)"
    return result
