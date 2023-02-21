"""
This is the flask default server backend
"""
import werkzeug
from nasse import config, servers


class Flask(servers.ServerBackend):
    """
    The default Flask server backend
    """

    def __init__(self, app: "Nasse", config: config.NasseConfig) -> None:
        self.app = app
        self.config = config or config.NasseConfig()
        self.server = None

    def run(self, *args, **kwargs):
        # kwargs.setdefault("use_reloader", self.config.debug)
        # kwargs.setdefault("use_debugger", self.config.debug)
        kwargs.setdefault("threaded", True)

        # make_server does not support `debug`
        kwargs.pop("debug", None)

        self.server = werkzeug.serving.make_server(
            host=self.config.host,
            port=self.config.port,
            app=self.app.flask,
            *args,
            **kwargs
        )
        self.server.serve_forever()

    def stop(self):
        if self.server is not None:
            self.server.shutdown()
