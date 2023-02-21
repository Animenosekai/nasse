"""
The Gunicorn backend

Note: Should be more suitable for production use
"""

import multiprocessing

from nasse import Nasse, config
from nasse.servers.flask import Flask

import gunicorn
import gunicorn.app.base
import gunicorn.arbiter


class Gunicorn(Flask):
    """
    The Gunicorn backend
    """
    class BaseApp(gunicorn.app.base.BaseApplication):
        """
        The internal Gunicorn base app
        """

        def __init__(self, app: Nasse, config: config.NasseConfig = None, **kwargs):
            self.app = app
            self.config = config or config.NasseConfig()
            self.options = {
                'bind': '{host}:{port}'.format(host=self.config.host, port=self.config.port),
                'workers': 2 * multiprocessing.cpu_count() + 1,
                'capture_output': False,
                'proc_name': self.app.id,
                'preload_app': True,
                'worker_class': "sync",
                'threads': 2 * multiprocessing.cpu_count() + 1,
                'loglevel': 'error',
                # would be painful to wait 30 seconds on each reload
                'graceful_timeout': 5 if self.config.debug else 20,
                'on_exit': self.on_exit,
                'on_starting': self.on_starting,
                **kwargs
            }
            self.options.update(kwargs or {})
            self.application = app.flask
            gunicorn.SERVER_SOFTWARE = self.config.server_header
            gunicorn.SERVER = gunicorn.SERVER_SOFTWARE
            super().__init__()

        def load_config(self):
            config = {key: value for key, value in self.options.items()
                      if key in self.cfg.settings and value is not None}
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.app.flask

        def on_starting(self, server):
            self.config.logger.log("Running the server ✨")

        def on_exit(self, server):
            self.config.logger.log("Exiting... 🏮")

    def __init__(self, app: Nasse, config: config.NasseConfig) -> None:
        super().__init__(app, config)
        self._arbiter = None

    def run(self, *args, **kwargs):
        gunicorn_handler = self.BaseApp(self.app, self.config, **kwargs)
        self._arbiter = gunicorn.arbiter.Arbiter(gunicorn_handler)
        self._arbiter.run()

    def stop(self, *args, **kwargs):
        if self._arbiter:
            self._arbiter.stop()
