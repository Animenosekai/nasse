from pathlib import Path

from nasse import docs, models


def make_docs(endpoint: models.Endpoint, postman: bool = False, curl: bool = True, javascript: bool = True, python: bool = True):
    result = '''
### {name}

> {description}
'''.format(name=endpoint.name, description=endpoint.description)
    if len(endpoint.methods) == 1:
        result += make_docs_for_method(endpoint=endpoint,
                                       method=list(endpoint.methods)[0])
    else:
        for method in endpoint.methods:
            result += '''\n- #### Using {method}\n{docs}'''.format(
                method=method, docs=make_docs_for_method(endpoint=endpoint, method=method, postman=postman, curl=curl, javascript=javascript, python=python))
    return result


def make_docs_for_method(endpoint: models.Endpoint, method: str, postman: bool = False, curl: bool = True, javascript: bool = True, python: bool = True):
    method = str(method)

    try:
        path = Path(endpoint.handler.__code__.co_filename).resolve(
        ).relative_to(Path().resolve())
    except Exception:
        path = Path(endpoint.handler.__code__.co_filename)
    line = endpoint.handler.__code__.co_firstlineno

    if not postman:
        result = '''
```http
{method} {path}
```

> [{source_code_path}]({github_path})
'''.format(method=method, path=endpoint.path, source_code_path=path, github_path="../{path}#L{line}".format(path=path, line=line))

    else:
        result = '''
> [{source_code_path}]({github_path})

{description}

'''.format(source_code_path=path, github_path="../{path}#L{line}".format(path=path, line=line), description=endpoint.description)

    result += '''
#### Authentication

'''
    if endpoint.login.no_login:
        result += "Login is **not** required"
    elif endpoint.login.required and (endpoint.login.all_methods or method in endpoint.login.methods):
        result += "Login{types} is **required**".format(
            types=(' with ' + ', '.join([str(type_name) for type_name in endpoint.login.types])) if len(endpoint.login.types) > 0 else "")
    elif endpoint.login.all_methods or method in endpoint.login.methods:
        result += "Login {types} is **optional**".format(
            types=(' with ' + ', '.join([str(type_name) for type_name in endpoint.login.types])) if len(endpoint.login.types) > 0 else "")
    else:
        result += "Login is **not** required"

    if endpoint.login.verification_only:
        result += " but only verified"

    if not postman:  # POSTMAN DOESN'T NEED THESE INFORMATION

        params = [param for param in endpoint.params if (
            param.all_methods or method in param.methods)]
        if len(params) > 0:
            result += '''

#### Parameters

| Name         | Description                      | Required         | Type             |
| ------------ | -------------------------------- | ---------------- | ---------------- |
'''
            result += "\n".join(
                ["| `{param}` | {description}  | {required}            | {type}            |".format(param=param.name, description=param.description, required=param.required, type=param.type.__name__ if param.type is not None else "str") for param in params])

        headers = [header for header in endpoint.headers if (
            header.all_methods or method in header.methods)]
        if len(headers) > 0:
            result += '''

#### Headers

| Name         | Description                      | Required         | Type             |
| ------------ | -------------------------------- | ---------------- | ---------------- |
'''
            result += "\n".join(
                ["| `{header}` | {description}  | {required}            | {type}            |".format(header=header.name, description=header.description, required=header.required, type=header.type.__name__ if header.type is not None else "str") for header in headers])

        cookies = [cookie for cookie in endpoint.cookies if (
            cookie.all_methods or method in cookie.methods)]
        if len(cookies) > 0:
            result += '''

#### Cookies

| Name         | Description                      | Required         | Type             |
| ------------ | -------------------------------- | ---------------- | ---------------- |
'''
            result += "\n".join(
                ["| `{cookie}` | {description}  | {required}            | {type}            |".format(cookie=cookie.name, description=cookie.description, required=cookie.required, type=cookie.type.__name__ if cookie.type is not None else "str") for cookie in cookies])

        dynamics = [dynamic for dynamic in endpoint.dynamics if (dynamic.all_methods or method in dynamic.methods)]
        if len(cookies) > 0:
            result += '''

#### Dynamic URL

| Name         | Description                      | Required         | Type             |
| ------------ | -------------------------------- | ---------------- | ---------------- |
'''
            result += "\n".join(
                ["| `{dynamic}` | {description}  | {required}            | {type}            |".format(dynamic=dynamic.name, description=dynamic.description, required=dynamic.required, type=dynamic.type.__name__ if cookie.type is not None else "str") for dynamic in dynamics])

        if any((curl, javascript, python)):
            result += '''

#### Example

<!-- tabs:start -->
'''
            if curl:
                result += '''
#### **cURL**

```bash
{curl}
```
'''.format(curl=docs.curl.create_curl_example_for_method(endpoint, method=method))

            if javascript:
                result += '''

#### **JavaScript**

```javascript
{javascript}
```
'''.format(javascript=docs.javascript.create_javascript_example_for_method(endpoint, method=method))

            if python:
                result += '''
#### **Python**

```python
{python}
```
'''.format(python=docs.python.create_python_example_for_method(endpoint, method=method))
            result += '''<!-- tabs:end -->'''

    returning = [element for element in endpoint.returning if (
        element.all_methods or method in element.methods)]
    if len(returning) > 0:
        if endpoint.json:
            result += '''
#### Response Format

```json
{example}
```
'''.format(example=docs.example.generate_example(endpoint, method=method))
        else:
            result += '''\nThis endpoint doesn't seem to return a JSON formatted response but rather will return data directly:\n'''

        result += '''
#### Returns

| Field        | Description                      | Type   | Nullable  |
| ----------   | -------------------------------- | ------ | --------- |
'''
        result += "\n".join(["| `{key}` | {description}  | {type}      | {nullable}      |".format(key=element.name,
                            description=element.description, type=docs.example._get_type(element), nullable=element.nullable) for element in returning])

    result += "\n"
    errors = [error for error in endpoint.errors if (
        error.all_methods or method in error.methods)]
    if len(errors) > 0:
        result += '''
#### Possible Errors

| Exception         | Description                      | Code   |
| ---------------   | -------------------------------- | ------ |
'''
        result += "\n".join(
            ["| `{key}` | {description}  | {code}  |".format(key=error.name, description=error.description, code=error.code) for error in errors])

    # result += "\n"
    return result
