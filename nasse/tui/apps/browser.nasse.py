"""Nasse's endpoints browser"""

import typing

from nasse import Endpoint
from nasse.tui.app import App


class Types:
    """Holds the different types used"""
    Categories = typing.Dict[str, typing.Dict[str, typing.List[Endpoint]]]


class Browser(App):
    """An endpoints browser"""

    def __init__(self, endpoints: typing.Optional[typing.List[Endpoint]] = None, **kwargs):
        super().__init__(**kwargs)
        self.endpoints = endpoints

    @property
    def categories(self) -> Types.Categories:
        """Returns the category separated endpoints"""
        mid_results: typing.Dict[str, typing.List[Endpoint]] = {}
        for endpoint in self.endpoints:
            try:
                mid_results[endpoint.category].append(endpoint)
            except KeyError:
                mid_results[endpoint.category] = [endpoint]

        results: Types.Categories = {}
        for category, endpoints in mid_results.items():
            results[category] = {}
            for endpoint in endpoints:
                try:
                    results[category][endpoint.sub_category or "@TopLevelEndpoint"].append(endpoint)
                except KeyError:
                    results[category][endpoint.sub_category or "@TopLevelEndpoint"] = [endpoint]
        return results
