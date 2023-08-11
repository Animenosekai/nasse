"""
Generates response examples
"""

from nasse import models, utils


def _get_type(data: models.Return) -> str:
    """
    An internal function to retrieves the type of the given returning item

    Parameters
    ----------
    data: models.Return
        The return value to get the type from

    Returns
    -------
    "string" | "int" | "float | "bool" | "array" | "object"
        The type, when possible
    str
        When impossible, returns the type as a string
    """
    key_type = data.type

    if key_type is None:
        example = data.example
        if example is None:
            return "string"
        if isinstance(example, type):
            return example.__name__
        elif isinstance(example, list):
            return "array"
        elif isinstance(example, dict):
            return "object"
        else:
            try:
                return example.__class__.__name__  # should be `str`
            except AttributeError:
                pass

    key_type = str(key_type)
    key_type_token = key_type.lower().replace(" ", "")
    if key_type_token in {"str", "string", "text"}:
        return "string"
    elif key_type_token in {"int", "integer"}:
        return "int"
    elif key_type_token in {"float", "floating", "number"}:
        return "float"
    elif key_type_token in {"bool", "true", "false", "boolean"}:
        return "bool"
    elif key_type_token in {"array", "list", "arr", "set"}:
        return "array"
    elif key_type_token in {"object", "obj", "dict", "dictionary"}:
        return "object"
    return key_type


def generate_example(endpoint: models.Endpoint, method: str) -> str:
    """
    Generates a JSON response example

    Parameters
    ----------
    endpoint: models.Endpoint
        The endpoint to get the response example from
    method: str
        The method to get the response example from

    Returns
    -------
    str
        The response example
    """
    def get_value(data):
        """

        Parameters
        ----------
        data
        """
        key_type = _get_type(data)
        # if self.returning[key].get("nullable", False) and key_type != "object":
        #    return None
        if key_type == "str":
            return str(data.example or "string")
        elif key_type == "int":
            return int(data.example or 4)
        elif key_type == "float":
            return float(data.example or 4.6)
        elif key_type == "array":
            return list(data.example or [])
        elif key_type == "bool":
            return utils.boolean.to_bool(data.example or True)
        elif key_type == "object":
            return {child.name: get_value(child) for child in data.children if (data.all_methods or method in data.methods)}
        return data.example or "no example"

    _response_format = {}
    for element in [data for data in models.get_method_variant(method, endpoint.returns) if "." not in data.name]:
        _response_format[element.name] = get_value(element)

    # we can't consider using f-strings because they came with py3.6
    # pylint: disable=consider-using-f-string
    return '''{{
    "success": true,
    "message": "Successfully processed your request",
    "error": null,
    "data": {response}
}}
'''.format(response=utils.json.encoder.encode(_response_format).replace("\n", "\n    "))
