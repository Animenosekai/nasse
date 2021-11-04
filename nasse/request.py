from typing import Any

from flask import request as flask_request
from werkzeug.datastructures import MultiDict

from nasse import exceptions, models
from nasse.config import General
from nasse.exceptions.request import MissingCookie, MissingHeader, MissingParam
from nasse.utils.ip import get_ip
from nasse.utils.sanitize import sanitize_text

_overwritten = {"nasse", "app", "nasse_endpoint",
                "client_ip", "method", "headers", "values", "args", "form", "params", "cookies"}


class Request(object):

    def __init__(self, app, endpoint: models.Endpoint) -> None:
        """
        A request object looking like the flask.Request one, but with the current endpoint in it and verification

        Example
        --------
        >>> from nasse import request
        # and then when processing the request #
        >>> request.nasse_endpoint
        Endpoint(path='/hello')
        >>> request.nasse_endpoint.name
        'Greeting Endpoint'

        Parameters
        ----------
            endpoint: Nasse.models.Endpoint
                The request's endpoint
        """
        if not isinstance(endpoint, models.Endpoint):
            raise exceptions.request.MissingEndpoint(
                "The current request doesn't have any Nasse endpoint")
        self.nasse = app
        self.app = self.nasse
        self.nasse_endpoint = endpoint

        self.client_ip = get_ip()

        self.method = flask_request.method.upper()

        # sanitize
        if General.SANITIZE_USER_SENT:
            self.values = MultiDict((key, sanitize_text(value))
                                    for key, value in flask_request.values.items(multi=True))
            #values.append((key, value.replace("<", "&lt").replace(">", "&gt")))
        else:
            self.values = MultiDict(flask_request.values.items(multi=True))
        self.params = self.values

        if General.SANITIZE_USER_SENT:
            self.args = MultiDict((key, sanitize_text(value))
                                  for key, value in flask_request.args.items(multi=True))
        else:
            self.args = MultiDict(flask_request.args.items(multi=True))

        if General.SANITIZE_USER_SENT:
            self.form = MultiDict((key, sanitize_text(value))
                                  for key, value in flask_request.form.items(multi=True))
        else:
            self.form = MultiDict(flask_request.form.items(multi=True))

        self.headers = MultiDict(flask_request.headers)
        self.cookies = MultiDict(flask_request.cookies)

        # verify if missing
        for attr, exception, current_values in [("params", MissingParam, self.values), ("headers", MissingHeader, self.headers), ("cookies", MissingCookie, self.cookies)]:
            for value in self.nasse_endpoint[attr]:
                if value.name not in current_values:
                    if value.required and (value.all_methods or self.method in value.methods):
                        raise exception(name=value.name)
                else:
                    if value.type is not None:
                        current_values[value.name] = value.type(
                            current_values[value.name])

    def __setattr__(self, name: str, value: Any) -> None:
        if name in _overwritten:
            return super().__setattr__(name, value)
        return flask_request.__setattr__(name, value)

    def __getattribute__(self, name: str) -> Any:
        if name in _overwritten:
            return super().__getattribute__(name)
        return flask_request._get_current_object().__getattribute__(name)
