"""
Runs the Nasse instances directly from the command line

TODO
----
- Running view
- Configurations view
- Statistical Monitoring
"""

from nasse import Nasse
from nasse.tui.app import App


def headless(app: Nasse, **kwargs):
    """The headless, non interactive version of the runner"""
    app.run(**kwargs)


class Runner(App):
    """The runner app"""
    pass
