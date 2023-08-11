"""
Creating `curl` examples
"""

import typing

from nasse import models


def create_curl_example_for_method(endpoint: models.Endpoint, method: str) -> str:
    """
    Creates a `curl` example for the given method

    Parameters
    ----------
    endpoint: models.Endpoint
        The endpoint to create the example from
    method: str
        The method to create the example for

    Returns
    -------
    str
        A usage example for `curl`
    """

    def sanitize_backslashes(element: str):
        """
        Turns the backslashes into triple backslashes

        Parameters
        ---------
        element: str
            The element to sanitize

        Returns
        -------
        str
            The sanitized element
        """
        return str(element).replace("\"", "\\\"")

    params = {param.name: param.description for param in models.get_method_variant(method, endpoint.parameters)}
    headers = {header.name: header.description for header in models.get_method_variant(method, endpoint.headers)}

    params_render = ""
    headers_render = ""

    if len(params) > 0:
        # ref: https://everything.curl.dev/http/post/url-encode
        params_render = "\\\n    --data-urlencode " + "\\\n    --data-urlencode ".join(
            ['"' + sanitize_backslashes(param)
             + '=<' + sanitize_backslashes(description)
             + '>"' for param, description in params.items()]
        ) + " "
        if len(headers) <= 0:
            params_render += "\\\n    "

    if len(headers) > 0:
        # ref: https://everything.curl.dev/http/requests/headers
        headers_render = "\\\n    -H " + '\\\n    -H '.join([
            '"' + sanitize_backslashes(header)
            + ': ' + sanitize_backslashes(description)
            + '"' for header, description in headers.items()]
        ) + " "
        headers_render += "\\\n    "

    return '''curl -X {method} {params}{headers}"{path}"'''.format(
        method=method,
        params=params_render,
        headers=headers_render,
        path=endpoint.path
    )


def create_curl_example(endpoint: models.Endpoint) -> typing.Dict[str, str]:
    """
    Creates a `curl` example command to use the endpoint.

    Parameters
    ----------
    endpoint: models.Endpoint
        The endpoint to create the example for

    Returns
    -------
    dict[str, str]
        A dictionary of {method: example} values.
    """
    results = {}
    for method in endpoint.methods:
        results[method] = create_curl_example_for_method(endpoint=endpoint, method=method)
    return results
