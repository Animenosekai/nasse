"""
Generates JavaScript examples
"""

import typing
import urllib.parse

from nasse import models, utils


def create_javascript_example_for_method(endpoint: models.Endpoint, method: str) -> str:
    """
    Creates a JavaScript example for the given method

    Parameters
    ----------
    endpoint: models.Endpoint
        The endpoint to create the example from
    method: str
        The method to get the example for

    Returns
    -------
    str
        A JavaScript example on how to use the endpoint for the given method
    """
    params = [param for param in models.get_method_variant(method, endpoint.parameters) if param.required]
    headers = {header.name: (header.description or header.name)
               for header in models.get_method_variant(method, endpoint.headers)
               if header.required}

    include_cookies = len(models.get_method_variant(method, endpoint.cookies)) > 0

    url = '"{path}"'.format(path=endpoint.path)

    if len(params) > 0:
        url = """`{path}?{params}`""".format(
            path=endpoint.path,
            params="&".join([
                '{escaped}=${{encodeURIComponent("{name}")}}'.format(
                    escaped=urllib.parse.quote(param.name),
                    name=param.name)
                for param in params]))

    headers_render = ""
    if len(headers) > 0:
        headers_render = ",\n    headers: {}".format(utils.json.encoder.encode(headers).replace("\n", "\n    "))

    return '''fetch({url}, {{
    method: "{method}"{headers}{cookies}
}})
.then((response) => {{response.json()}})
.then((response) => {{
    if (response.success) {{
        console.info("Successfully requested for {path}")
        console.log(response.data)
    }} else {{
        console.error("An error occured while requesting for {path}, error: " + response.error)
    }}
}})'''.format(url=url, method=method, headers=headers_render, cookies=",\n    credentials: 'include'" if include_cookies else "", path=endpoint.path)


def create_javascript_example(endpoint: models.Endpoint) -> typing.Dict[str, str]:
    """
    Creates JavaScript examples for the given endpoint

    Parameters
    ----------
    endpoint: models.Endpoint
        The endpoint to get the example for

    Returns
    -------
    """
    results = {}
    for method in endpoint.methods:
        results[method] = create_javascript_example_for_method(endpoint=endpoint,
                                                               method=method)
    return results
