import dataclasses
import pathlib
import typing
import urllib.parse

from nasse.utils.annotations import Default


def _alphabetic(l):
    return "".join(l for l in str(string) if l.isalpha() or l.isdecimal())


@dataclasses.dataclass
class NasseConfig:
    def verify_logger(self):
        from nasse.utils.logging import Logger
        if self.logger is None:
            self.logger = Logger()

    def __post_init__(self):
        from nasse.utils.logging import LoggingLevel

        if isinstance(self.id, Default):
            self.id = str(self.id or _alphabetic(self.app).lower())
        
        self.verify_logger()

        if isinstance(self.logging_level, Default):
            self.logging_level = LoggingLevel.DEBUG if self.debug else LoggingLevel.INFO

        if isinstance(self.log_file, Default):
            self.log_file = (pathlib.Path() / "NASSE_DEBUG" / "nasse.log") if self.debug else None

        if isinstance(self.cors, str):
            rule = str(self.cors).replace(" ", "")
            if rule == "*":
                self.cors = ["*"]
            else:
                parsed = urllib.parse.urlparse(rule)
                netloc = parsed.netloc if parsed.netloc else parsed.path.split(
                    "/")[0]
                scheme = parsed.scheme or "https"
                rule = '{scheme}://{netloc}'.format(
                    scheme=scheme, netloc=netloc)
                self.cors = [rule]
        elif isinstance(self.cors, bool):
            self.cors = ["*"] if self.cors else []
        else:
            self.cors = []
            for rule in self.cors:
                rule = str(rule).replace(" ", "")
                if rule == "*":
                    self.cors.append("*")
                    continue
                else:
                    parsed = urllib.parse.urlparse(rule)
                    netloc = parsed.netloc if parsed.netloc else parsed.path.split("/")[0]
                    scheme = parsed.scheme or "https"
                    rule = '{scheme}://{netloc}'.format(scheme=scheme, netloc=netloc)
                    self.cors.append(rule)

    app: str = "Nasse"
    id: str = Default(None)
    host: str = "127.0.0.1"
    port: int = 5000
    debug: bool = False
    account_management = None
    cors: typing.Union[str, bool, typing.Iterable] = True
    max_request_size: int = 1e+9
    compress: bool = True
    log_file: pathlib.Path = Default(None)
    logging_level: "LoggingLevel" = Default("LoggingLevel.INFO")
    logger: "Logger" = None
    server_header: str = "Nasse/{version} ({app})"
    sanitize_user_input: bool = True
    base_dir: pathlib.Path = pathlib.Path().resolve().absolute()
