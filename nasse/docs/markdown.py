from pathlib import Path

from nasse import docs, models


def make_docs(endpoint: models.Endpoint, postman: bool = False):
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
                method=method, docs=make_docs_for_method(endpoint=endpoint, method=method, postman=postman))
    return result


def make_docs_for_method(endpoint: models.Endpoint, method: str, postman: bool = False):
    method = str(method)

    try:
        path = Path(endpoint.handler.__code__.co_filename).resolve(
        ).relative_to(Path().resolve())
    except Exception:
        path = Path(endpoint.handler.__code__.co_filename)

    if not postman:
        result = '''
```http
{method} {path}
```

> [{source_code_path}]({github_path})
'''.format(method=method, path=endpoint.path, source_code_path=path, github_path="../" + path)

    else:
        result = '''
> [{source_code_path}]({github_path})

{description}

'''.format(source_code_path=path, github_path="../" + path, description=endpoint.description)

    result += '''
#### Authentication

'''
    if endpoint.login.no_login:
        result += "Login is **not** required"
    elif endpoint.login.required and (endpoint.login.all_methods or method in endpoint.login.methods):
        result += "Login with {types} is **required**".format(
            types=', '.join([str(type_name) for type_name in endpoint.login.types]))
    elif endpoint.login.all_methods or method in endpoint.login.methods:
        result += "Login with {types} is **optional**".format(
            types=', '.join([str(type_name) for type_name in endpoint.login.types]))
    else:
        result += "Login is **not** required"

    if not postman:  # POSTMAN DOESN'T NEED THESE INFORMATION

        params = [param for param in endpoint.params if (
            param.all_methods or method in param.methods)]
        if len(params) > 0:
            result += '''

#### Parameters

| Name         | Description                      | Required         |
| ------------ | -------------------------------- | ---------------- |
'''
            result += "\n".join(
                ["| `{param}` | {description}  | {required}            |".format(param=param.name, description=param.description, required=param.required) for param in params])

        headers = [header for header in endpoint.headers if (
            header.all_methods or method in header.methods)]
        if len(headers) > 0:
            result += '''

#### Headers

| Name         | Description                      | Required         |
| ------------ | -------------------------------- | ---------------- |
'''
            result += "\n".join(
                ["| `{header}` | {description}  | {required}            |".format(header=header.name, description=header.description, required=header.required) for header in headers])

        result += '''

#### Example

<!-- tabs:start -->

#### **cURL**

```bash
{curl}
```

#### **JavaScript**

```javascript
{javascript}
```

#### **Python**

```python
{python}
```

<!-- tabs:end -->'''.format(curl=docs.curl.create_curl_example_for_method(endpoint, method=method), javascript=docs.javascript.create_javascript_example_for_method(endpoint, method=method), python=docs.python.create_python_example_for_method(endpoint, method=method))

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
