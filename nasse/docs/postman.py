import typing
from copy import deepcopy
# from uuid import uuid4

from nasse import docs, models
from nasse.utils.sanitize import sort_http_methods


def create_postman_data(app, section: str, endpoints: typing.List[models.Endpoint]):
    postman_section = {
        "info": {
            # "_postman_id": str(uuid4()),
            "name": section,
            "description": "All of the endpoints under the '{section}' section of the {name} API Interface".format(section=section, name=app.name),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [],
        "auth": {
            "type": "apikey",
            "apikey": [
                {
                    "key": "value",
                    "value": "{{{{{id}_TOKEN}}}}".format(id=app.id.upper()),
                    "type": "string"
                },
                {
                    "key": "key",
                    "value": "Authorization",
                    "type": "string"
                }
            ]
        }
    }
    for endpoint in endpoints:
        postman_section["item"].extend(create_postman_docs(endpoint))
    return postman_section


def create_postman_docs(endpoint: models.Endpoint):
    results = []
    for method in sort_http_methods(endpoint.methods):
        result = {
            "name": str(endpoint.name),
            "event": [],
            "request": {
                "method": str(method).upper(),
                "header": [
                    {
                        "key": header.name,
                        "value": header.description or header.name,
                        "type": "text"
                    }
                    for header in endpoint.headers if header.all_methods or method in header.methods],
                "url": {
                    "raw": "{{DOMAIN}}" + endpoint.path.replace("<", "{{").replace(">", "}}") + "?=" + '&'.join([param.name for param in endpoint.params if param.all_methods or method in param.methods]),
                    "host": [
                        "{{DOMAIN}}"
                    ],
                    "path": [elem.replace("<", "{{").replace(">", "}}") for elem in endpoint.path.split("/") if elem != ""],
                    "query": [
                        {
                            "key": param.name,
                            "value": "<{param}:{type}>".format(param=param.name, type=param.type.__name__ if hasattr(param.type, "__name__") else str(param.type) if param.type is not None else "str"),
                            "description": param.description or param.name
                        }
                        for param in endpoint.params if param.all_methods or method in param.methods]
                },
                "description": docs.markdown.make_docs_for_method(endpoint=endpoint, method=method, postman=True)
            },
            "response": []
        }
        result["response"].append(deepcopy(result))
        result["response"][0]["status"] = "OK"
        result["response"][0]["code"] = 200
        result["response"][0]["_postman_previewlanguage"] = "json"
        result["response"][0]["header"] = []
        result["response"][0]["cookie"] = []
        result["response"][0]["body"] = docs.example.generate_example(
            endpoint=endpoint, method=method)

        login_rules = endpoint.login.get(method, endpoint.login.get("*", None))

        if login_rules is None or login_rules.no_login:
            result["request"]["auth"] = {
                "type": "noauth"
            }

        results.append(result)

    return results
