from uuid import uuid4
from copy import deepcopy
from nasse.docs.example import generate_example

from nasse.models import Endpoint


def create_postman_data(app, section: str, endpoints: list[Endpoint]):
    postman_section = {
        "info": {
            "_postman_id": str(uuid4()),
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


def create_postman_docs(endpoint: Endpoint):
    results = []
    for method in endpoint.methods:
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
                            "value": "<{param}>".format(param=param.name),
                            "description": param.description or param.name
                        }
                        for param in endpoint.params if param.all_methods or method in param.methods]
                },
                "description": create_postman_description(endpoint=endpoint, method=method)
            },
            "response": []
        }
        result["response"].append(deepcopy(result))
        result["response"][0]["status"] = "OK"
        result["response"][0]["code"] = 200
        result["response"][0]["_postman_previewlanguage"] = "json"
        result["response"][0]["header"] = []
        result["response"][0]["cookie"] = []
        result["response"][0]["body"] = generate_example(
            endpoint=endpoint, method=method)

        if not endpoint.login.all_methods and method not in endpoint.login.methods:
            result["request"]["auth"] = {
                "type": "noauth"
            }

        results.append(result)

    return results


def create_postman_description(endpoint: Endpoint, method: str):
    pass