def header_link(header: str, registry: list[str]):
    """
    - All text is converted to lowercase.
    - All non-word text (e.g., punctuation, HTML) is removed.
    - All spaces are converted to hyphens.
    - Two or more hyphens in a row are converted to one.
    - If a header with the same ID has already been generated, a unique incrementing number is appended, starting at 1.
    """
    registry = registry
    result = "".join(l for l in str(header) if l.isalpha()
                     or l.isdecimal() or l == " ")
    result = result.replace(" ", "-").lower()
    final_result = ""
    for index, letter in enumerate(result):
        if letter == "-" and index > 0 and result[index - 1] != '-':
            final_result += letter
        elif index <= 0 and letter != '-':
            final_result = letter
        elif index > 0 and letter != '-':
            final_result += letter
    link_count = registry.count(final_result)
    registry.append(final_result)
    if link_count > 0:
        return "{result}-{count}".format(result=final_result, count=link_count)
    else:
        return final_result


DOCS_HEADER = '''
# {name} API Reference

Welcome to the {name} API Reference.

## Globals

### Response Format

Globally, JSON responses should be formatted as follows (even when critical errors occur)

```json
{{
    "success": true,
    "error": null,
    "data": {{}}
}}
```

| Field        | Description                                      | Nullable         |
| ------------ | ------------------------------------------------ | ---------------- |
| `success`    | Wether the request was a success or not          | False            |
| `error`      | The exception name if an error occured           | True             |
| `data`       | The extra data, information asked in the request | False            |

### Errors

Multiple Errors can occur, server side or request side.

Specific errors are documented in each endpoint but these are the general errors that can occur on any endpoint:

| Exception                   | Description                                                                   | Code  |
| --------------------------- | ----------------------------------------------------------------------------- | ----- |
| `SERVER_ERROR`              | When an error occurs on Anime Terebi while processing a request               | 500   |
| `INTERNAL_SERVER_ERROR`     | When a critical error occurs on the system                                    | 500   |
| `METHOD_NOT_ALLOWED`        | When you made a request with the wrong method                                 | 405   |
| `MISSING_HEADER`            | When a required header is missing or is empty                                 | 400   |
| `MISSING_PARAM`             | When a required parameter (form value or url param) is missing or is empty    | 400   |
| `AUTH_ERROR`                | When an error occured while authentificating the request                      | 401   |
| `TOKEN_USE_MISMATCH`        | When the `use` field in the JWT is not the one needed for the request         | 401   |
| `EXPIRED_TOKEN`             | When the given JWT is expired                                                 | 401   |
| `ACCOUNT_NOT_FOUND`         | When the account associated with the token is not found in our database       | 404   |

### Authenticated Requests

When a user needs to be logged in, the "Authorization" header needs to be set to the login token provided when logging in.

A lookup for the account will be made on each authentificated request.

Alternatively, the "{id}_token" parameter and "__{id}_token" cookie can be used but these won't be prioritized.

### Debug Mode

On debug mode (`-d` or `--debug`), multiple information are passed in the `debug` section of the response and the `DEBUG` log level is selected on the server.

The 'debug' section is available on every type of error, except the ones issued by Flask such as `INTERNAL_SERVER_ERROR`, `METHOD_NOT_ALLOWED`, etc. (they need to do the bare minimum to not raise an exception and therefore breaking the server)

Look at [flask_exceptions.json](./flask_exceptions.json) for a list of Flask issued exceptions.

The "call_stack" attribute is enabled only when an error occurs or the `call_stack` parameter is passed with the request.

```json
{{
    "success": true,
    "error": null,
    "data": {{
        "username": "Animenosekai"
    }},
    "debug": {{
        "time": {{
            "global": 0.036757,
            "verification": 0.033558,
            "authentication": 0.003031,
            "processing": 4.9e-05,
            "formatting": 0.0001
        }},
        "ip": "127.0.0.1",
        "headers": {{
            "Host": "api.{id}.com",
            "Connection": "close",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr-fr",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15"
        }},
        "values": {{}},
        "domain": "api.{id}.com",
        "logs": [
            "1636562693.036563｜[INFO] [nasse.receive.Receive.__call__] → Incoming GET request to /account/name from 127.0.0.1",
            "1636562693.070008｜[ERROR] [nasse.exceptions.base.MissingToken.__init__] An authentication token is missing from the request"
        ],
        "call_stack": [
            "pass the 'call_stack' parameter to get the call stack"
        ]
    }}
}}
```

'''
