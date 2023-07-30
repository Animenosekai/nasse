"""
The base strings
"""
import pathlib
import inspect


# We are using a special `classproperty` because
# the chaining of `@property` and `@classmethod`
# got deprecated in 3.11
class classproperty(property):
    """A class property"""

    def __get__(self, owner_self, owner_cls):
        if self.fget:
            return self.fget(owner_cls)


class Localization:
    """
    Represents a Nasse documentation generation localization
    """
    __native__ = "Base"
    """The native name for the localization language"""

    @classproperty
    def __id__(cls):  # pylint: disable=no-self-argument
        return pathlib.Path(inspect.getfile(cls)).stem

    @classproperty
    def __english__(cls):  # pylint: disable=no-self-argument
        # Might change this later to support MultipleCaseNames
        # pylint: disable=no-member
        return cls.__name__.lower().removesuffix("localization").title()

    sections = "Sections"
    getting_started = "Getting Started"

    yes = "Yes"
    no = "No"

    no_description = "No description"
    using_method = "Using {method}"

    # Authentication
    authentication = "Authentication"
    no_auth_rule = "There is no authentication rule defined"
    no_login = "Login is **not** required"
    login_with_types_required = "Login with {types} is **required**"
    login_with_types_optional = "Login with {types} is **optional**"
    login_required = "Login is **required**"
    login_optional = "Login is **optional**"
    login_suffix_only_verified = " but only verified"

    # User sent values
    parameters = "Parameters"
    headers = "Headers"
    cookies = "Cookies"
    dynamic_url = "Dynamic URL"

    name = "Name"
    description = "Description"
    required = "Required"
    type = "Type"

    # Example
    example = "Example"

    # Response
    response = "Response"
    example_response = "Example response"
    not_json_response = "This endpoint doesn't seem to return a JSON-formatted response."

    # Response description
    returns = "Returns"
    field = "Field"
    nullable = "Nullable"

    # Errors
    possible_errors = "Possible Errors"
    exception = "Exception"
    code = "Code"

    # Index
    index = "Index"
    return_to_index = "Return to the Index"

    # Postman
    postman_description = "All of the endpoints under the '{section}' section of the {name} API Interface"

    # Headers
    getting_started_header = '''
# {name} API Reference

Welcome to the {name} API Reference.

## Globals

### Response Format

Globally, JSON responses should be formatted as follows (even when critical errors occur)

```json
{{
    "success": true,
    "message": "We successfully did this!",
    "error": null,
    "data": {{}}
}}
```

| Field        | Description                                      | Nullable         |
| ------------ | ------------------------------------------------ | ---------------- |
| `success`    | Whether the request was a success or not         | No               |
| `message`    | A message describing what happened               | Yes              |
| `error`      | The exception name if an error occurred          | Yes              |
| `data`       | The extra data, information asked in the request | No               |

### Errors

Multiple Errors can occur, server side or request side.

Specific errors are documented in each endpoint, but these are the general errors that can occur on any endpoint:

| Exception                   | Description                                                                                                     | Code  |
| --------------------------- | --------------------------------------------------------------------------------------------------------------- | ----- |
| `SERVER_ERROR`              | When an error occurs on {name} while processing a request                                                       | 500   |
| `MISSING_CONTEXT`           | When you are trying to access something which is only available in a Nasse context, and you aren't in one       | 500   |
| `INTERNAL_SERVER_ERROR`     | When a critical error occurs on the system                                                                      | 500   |
| `METHOD_NOT_ALLOWED`        | When you made a request with the wrong method                                                                   | 405   |
| `CLIENT_ERROR`              | When something is missing or is wrong with the request                                                          | 400   |
| `INVALID_TYPE`              | When Nasse couldn't convert the given value to the right type                                                   | 400   |
| `MISSING_VALUE`             | When a value is missing from the request                                                                        | 400   |
| `MISSING_PARAM`             | When a parameter is missing from the request                                                                    | 400   |
| `MISSING_DYNAMIC`           | When a dynamic routing value is missing from the requested URL                                                  | 400   |
| `MISSING_HEADER`            | When a header is missing from the request                                                                       | 400   |
| `MISSING_COOKIE`            | When a cookie is missing from the request                                                                       | 400   |
| `AUTH_ERROR`                | When an error occurred while authenticating the request                                                         | 403   |

### Authenticated Requests

When a user needs to be logged in, the "Authorization" header needs to be set to the login token provided when logging in.

Alternatively, the "{id}_token" parameter and "__{id}_token" cookie can be used, but these won't be prioritized.

If the endpoint is flagged for a "verified only" login, the account won't be fetched from any database, but the token will be checked.

### Debug Mode

On debug mode (`-d` or `--debug`), multiple information are passed in the `debug` section of the response and the `DEBUG` log level is selected on the server.

The 'debug' section is available on every type of error, except the ones issued by Flask such as `INTERNAL_SERVER_ERROR`, `METHOD_NOT_ALLOWED`, etc. (they need to do the bare minimum to not raise an exception and therefore breaking the server)

The "call_stack" attribute is enabled only when an error occurs or the `call_stack` parameter is passed with the request.

```json
{{
    "success": true,
    "message": "We couldn't fullfil your request",
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

    section_header = '''
# {name} Section API Reference

This file lists and explains the different endpoints available in the {name} section.
'''

    # TUI

    # Footer
    tui_history = "History"
    tui_result = "Result"
    tui_explorer = "Explorer"
    tui_submit = "Submit"
    tui_options = "Options"
    tui_quit = "Quit"

    # History
    # WARNING: This should stay under 3 characters to avoid having styling issues
    tui_min = "Min"
    tui_average = "Avg"
    tui_max = "Max"

    # Explorer
    tui_reset = "Reset"

    # Request
    tui_request = "Request"
    tui_name = "name"
    tui_value = "value"
    tui_path = "path"
    # tui_parameters = "Parameters"
    # tui_headers = "Headers"
    # tui_cookies = "Cookies"
    tui_file = "File"
    tui_add_file = "Add File"
    tui_data = "Data"
    tui_add_data_file = "Add Data File"

    # Options
    tui_language = "Language"
    tui_language_notice = "You need to restart the app to apply the changes"
    tui_base_url = "Base URL"
    tui_base_url_placeholder = "the base url for the requests and the endpoints explorer"
    tui_endpoints_update = "Endpoints Update"
    tui_endpoints_update_placeholder = "time between each endpoints list update (in sec.)"
    tui_history_limit = "History Limit"
    tui_history_limit_placeholder = "maximum number of requests in the history"
    tui_timeout = "Timeout"
    tui_timeout_placeholder = "timeout (sec.)"
    tui_redirects = "Redirects"
    tui_allow_redirects = "Allow Redirects"
    tui_proxies = "Proxies"
    tui_security = "Security"
    tui_verify_request = "Verify Request"
    tui_certificate_files = "Certificate Files"
    tui_add_certificate = "Add Certificate"

    # Result
    tui_start_prompt = "Start by making a request"
    tui_content = "Content"
    tui_no_content = "Can't display the content"
    tui_contacting = "Contacting {url}"
    tui_files = "Files"
    tui_error = "Error"

    # File Explorer
    tui_filter = "Filter"

    # Quit
    tui_quit_confirmation = "Are you sure you want to quit?"
    tui_cancel = "Cancel"
