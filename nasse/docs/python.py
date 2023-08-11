"""
Generates Python usage examples
"""

import json
import typing

from nasse import models


def create_python_example_for_method(endpoint: models.Endpoint, method: str) -> str:
    """
    Generates a Python example for the given endpoint

    Parameters
    ----------
    endpoint: models.Endpoint
        The endpoint to create the example for
    method: str
        The method to create the example for

    Returns
    -------
    str
        The example
    """
    
    params = {param.name: (param.description or param.name)
               for param in models.get_method_variant(method, endpoint.parameters)
               if param.required}
    headers = {header.name: (header.description or header.name)
               for header in models.get_method_variant(method, endpoint.headers)
               if header.required}

    params_render = ""
    headers_render = ""

    if len(params) > 0:
        params_render = ",\n        params = {}".format(json.dumps(params,
                                                                   ensure_ascii=False,
                                                                   indent=4)
                                                        .replace("\n", "\n        "))

    if len(headers) > 0:
        headers_render = ",\n        headers = {}".format(json.dumps(headers,
                                                                     ensure_ascii=False,
                                                                     indent=4)
                                                          .replace("\n", "\n        "))

    return '''import requests
r = requests.request("{method}", "{path}"{params}{headers})
if r.status_code >= 400 or not r.json()["success"]:
    raise ValueError("An error occured while requesting for {path}, error: " + r.json()["error"])
print("Successfully requested for {path}")
print(r.json()["data"])'''.format(method=method,
                                  path=endpoint.path,
                                  params=params_render,
                                  headers=headers_render)


def create_python_example(endpoint: models.Endpoint) -> typing.Dict[str, str]:
    """
    Generates Python examples for the given endpoint

    Parameters
    ----------
    endpoint: models.Endpoint
        The endpoint to create the example for

    Returns
    -------
    dict[str, str]
        A dictionary containing {method: example} values
    """
    results = {}
    for method in endpoint.methods:
        results[method] = create_python_example_for_method(endpoint=endpoint,
                                                           method=method)
    return results
