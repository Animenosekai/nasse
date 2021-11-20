import typing

import flask
import werkzeug.datastructures

from nasse import config, exceptions, models, utils

_overwritten = {"nasse", "app", "nasse_endpoint",
                "client_ip", "method", "headers", "values", "args", "form", "params", "cookies"}


class Request(object):

    def __init__(self, app, endpoint: models.Endpoint, dynamics: dict = {}) -> None:
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

        self.client_ip = utils.ip.get_ip()

        self.method = flask.request.method.upper()

        # sanitize
        if config.General.SANITIZE_USER_SENT:
            self.values = werkzeug.datastructures.MultiDict((key, utils.sanitize.sanitize_text(value))
                                                            for key, value in flask.request.values.items(multi=True))
            #values.append((key, value.replace("<", "&lt").replace(">", "&gt")))
        else:
            self.values = werkzeug.datastructures.MultiDict(
                flask.request.values.items(multi=True))
        self.params = self.values

        if config.General.SANITIZE_USER_SENT:
            self.args = werkzeug.datastructures.MultiDict((key, utils.sanitize.sanitize_text(value))
                                                          for key, value in flask.request.args.items(multi=True))
        else:
            self.args = werkzeug.datastructures.MultiDict(
                flask.request.args.items(multi=True))

        if config.General.SANITIZE_USER_SENT:
            self.form = werkzeug.datastructures.MultiDict((key, utils.sanitize.sanitize_text(value))
                                                          for key, value in flask.request.form.items(multi=True))
        else:
            self.form = werkzeug.datastructures.MultiDict(
                flask.request.form.items(multi=True))

        if config.General.SANITIZE_USER_SENT:
            self.dynamics = werkzeug.datastructures.MultiDict((key, utils.sanitize.sanitize_text(value))
                                                              for key, value in dynamics.items())
        else:
            self.dynamics = werkzeug.datastructures.MultiDict(dynamics.items())

        self.headers = werkzeug.datastructures.MultiDict(flask.request.headers)
        self.cookies = werkzeug.datastructures.MultiDict(flask.request.cookies)

        # verify if missing
        for attr, exception, current_values in [("params", exceptions.request.MissingParam, self.values), ("headers", exceptions.request.MissingHeader, self.headers), ("cookies", exceptions.request.MissingCookie, self.cookies), ("dynamics", exceptions.request.MissingDynamic, self.dynamics)]:
            for value in self.nasse_endpoint[attr]:
                if value.name not in current_values:
                    if value.required and (value.all_methods or self.method in value.methods):
                        raise exception(name=value.name)
                else:
                    if value.type is not None:
                        results = []
                        for key, val in current_values.items(multi=True):
                            if key == value.name:
                                results.append(value.type(val))
                        current_values.setlist(value.name, results)

    def __setattr__(self, name: str, value: typing.Any) -> None:
        if name in _overwritten:
            return super().__setattr__(name, value)
        return flask.request.__setattr__(name, value)

    def __getattribute__(self, name: str) -> typing.Any:
        if name in _overwritten:
            return super().__getattribute__(name)
        return flask.request._get_current_object().__getattribute__(name)
