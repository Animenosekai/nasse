import json

from nasse import models


def create_python_example_for_method(endpoint: models.Endpoint, method: str):
    params = {param.name: param.description or param.name for param in endpoint.params if param.required and (
        param.all_methods or method in param.methods)}
    headers = {header.name: header.description or header.name for header in endpoint.headers if header.required and (
        header.all_methods or method in header.methods)}
    params_render = ""
    headers_render = ""
    if len(params) > 0:
        params_render = ",\n        params = {render}".format(render=json.dumps(
            params, ensure_ascii=False, indent=4).replace("\n", "\n        "))
    if len(headers) > 0:
        headers_render = ",\n        headers = {render}".format(render=json.dumps(
            headers, ensure_ascii=False, indent=4).replace("\n", "\n        "))

    return '''import requests
r = requests.request("{method}", "{path}"{params}{headers})
if r.status_code >= 400 or not r.json()["success"]:
    raise ValueError("An error occured while requesting for {path}, error: " + r.json()["error"])
print("Successfully requested for {path}")
print(r.json()["data"])'''.format(method=method, path=endpoint.path, params=params_render, headers=headers_render)


def create_python_example(endpoint: models.Endpoint):
    results = {}
    for method in endpoint.methods:
        results[method] = create_python_example_for_method(
            endpoint=endpoint, method=method)
    return results
