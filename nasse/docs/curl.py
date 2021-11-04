from nasse import models


def create_curl_example_for_method(endpoint: models.Endpoint, method: str):
    params = {param.name: param.description or param.name for param in endpoint.params if param.required and (
        param.all_methods or method in param.methods)}
    headers = {header.name: header.description or header.name for header in endpoint.headers if header.required and (
        header.all_methods or method in header.methods)}
    params_render = ""
    headers_render = ""
    if len(params) > 0:
        params_render = "\\\n    --data-urlencode " + "\\\n    --data-urlencode ".join(['"' + param.replace(
            "\"", "\\\"") + '=<' + description.replace("\"", "\\\"") + '>"' for param, description in params.items()]) + " "
        if len(headers) <= 0:
            params_render += "\\\n    "
    if len(headers) > 0:
        headers_render = "\\\n    -H " + '\\\n    -H '.join(['"' + header.replace(
            "\"", "\\\"") + ': ' + description.replace("\"", "\\\"") + '"' for header, description in headers.items()]) + " "
        headers_render += "\\\n    "
    return '''curl -X {method} {params}{headers}"{path}"'''.format(
        method=method, params=params_render, headers=headers_render, path=endpoint.path)


def create_curl_example(endpoint: models.Endpoint):
    results = {}
    for method in endpoint.methods:
        results[method] = create_curl_example_for_method(
            endpoint=endpoint, method=method)
    return results
