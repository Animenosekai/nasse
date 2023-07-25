"""
Generates docs for Postman
"""

import typing
from copy import deepcopy
# from uuid import uuid4

from nasse import docs, models
from nasse.localization.base import Localization
from nasse.utils.sanitize import sort_http_methods


def create_postman_data(app, section: str, endpoints: typing.List[models.Endpoint], localization: Localization = Localization()) -> typing.Dict[str, typing.Any]:
    """
    Generates the data for postman

    Parameters
    ----------
    app
    section: str
        The section to document
    endpoint: list[models.Endpoint]
        A list of endpoints
    localization: Localization
        The language of the docs

    Returns
    -------
    dict[str, Any]
        The data for Postman
    """
    postman_section = {
        "info": {
            # "_postman_id": str(uuid4()),
            "name": section,
            "description": localization.postman_description.format(section=section, name=app.config.name),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [],
        "auth": {
            "type": "apikey",
            "apikey": [
                {
                    "key": "value",
                    "value": "{{{{{id}_TOKEN}}}}".format(id=app.config.id.upper()),
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
        postman_section["item"].extend(create_postman_docs(endpoint, localization=localization))
    return postman_section


def create_postman_docs(endpoint: models.Endpoint, localization: Localization = Localization()):
    """
    Generates the Postman docs for an endpoint

    Parameters
    ----------
    endpoint: models.Endpoint
        The endpoint to generate the docs for
    localization: Localization
        The language to use

    Returns
    -------
    list[dict[str, Any]]
        A list of documentation data for Postman (one item per method)
    """
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
                    for header in models.get_method_variant(method, endpoint.headers)],
                "url": {
                    "raw": "{{DOMAIN}}" + endpoint.path.replace("<", "{{").replace(">", "}}") + "?=" + '&'.join([param.name for param in models.get_method_variant(method, endpoint.parameters)]),
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
                        for param in models.get_method_variant(method, endpoint.parameters)]
                },
                "description": docs.markdown.make_docs_for_method(endpoint=endpoint, method=method, postman=True, localization=localization)
            },
            "response": []
        }
        result["response"].append(deepcopy(result))
        result["response"][0]["status"] = "OK"
        result["response"][0]["code"] = 200
        if endpoint.json:
            result["response"][0]["_postman_previewlanguage"] = "json"
        result["response"][0]["header"] = []
        result["response"][0]["cookie"] = []
        result["response"][0]["body"] = docs.example.generate_example(
            endpoint=endpoint, method=method)

        login_rules = endpoint.login.get(method, endpoint.login["*"])

        for rule in login_rules:
            if rule.skip:
                result["request"]["auth"] = {
                    "type": "noauth"
                }
                break
        results.append(result)

    return results
