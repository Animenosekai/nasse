"""
Nasse configuration
"""

import dataclasses
import pathlib
import typing
import urllib.parse
from nasse.utils import formatter
from nasse import __info__

def _alphabetic(string):
    return "".join(l for l in str(string) if l.isalpha() or l.isdecimal())


@dataclasses.dataclass
class NasseConfig:
    """
    A configuration object for a Nasse app
    """

    def verify_logger(self):
        """Verifies the logger"""
        from nasse.utils.logging import Logger
        if self.logger is None:
            self.logger = Logger(self)
            # self.logger = Logger()

    def verify_logging_level(self):
        """Verifies the given logging level"""
        from nasse.utils.logging import LoggingLevel

        if isinstance(self.logging_level, LoggingLevel):
            level_name = self.logging_level.name
        else:
            level_name = str(self.logging_level)

        level_name = level_name.upper().replace(" ", "")

        if not self.logging_level:
            self.logging_level = LoggingLevel.DEBUG if self.debug else LoggingLevel.INFO
        elif level_name == "ERROR":
            self.logging_level = LoggingLevel.ERROR
        elif level_name == "WARNING":
            self.logging_level = LoggingLevel.WARNING
        elif level_name == "INFO":
            self.logging_level = LoggingLevel.INFO
        elif level_name == "DEBUG":
            self.logging_level = LoggingLevel.DEBUG
        elif level_name == "HIDDEN":
            self.logging_level = LoggingLevel.HIDDEN
        else:
            try:
                self.logger.warn(f"Couldn't understand the logging level {self.logging_level}. Defaulting to `INFO`")
            except Exception:
                pass
            self.logging_level = LoggingLevel.INFO

    def __setattr__(self, __name: str, __value: typing.Any) -> None:
        if __name == "debug" and (not isinstance(self.logging_level, str)) and (not self.logging_level or self.logging_level.value < 4):
            from nasse.utils.logging import LoggingLevel
            if __value:
                self.logging_level = LoggingLevel.DEBUG
            else:
                self.logging_level = LoggingLevel.INFO
        super().__setattr__(__name, __value)

    def __post_init__(self):
        # self.VERSION = __info__.__version__

        if not self.id:
            self.id = _alphabetic(self.name).lower()

        self.verify_logger()
        self.verify_logging_level()

        if not self.log_file:
            self.log_file = (pathlib.Path() / ".nasse" / "debug" / "log") if self.debug else None

        if isinstance(self.cors, str):
            rule = str(self.cors).replace(" ", "")
            if rule == "*":
                self.cors = ["*"]
            else:
                parsed = urllib.parse.urlparse(rule)
                netloc = (parsed.netloc if parsed.netloc
                          else parsed.path.split("/")[0])
                scheme = parsed.scheme or "https"
                rule = f'{scheme}://{netloc}'
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
                    rule = f'{scheme}://{netloc}'
                    self.cors.append(rule)

        self.server_header = formatter.format(self.server_header, config=self)

    name: str = "Nasse"
    id: typing.Optional[str] = None # pylint: disable=invalid-name
    host: str = "127.0.0.1"
    port: int = 5005
    debug: bool = False
    account_management: typing.Optional["AccountManagement"] = None
    cors: typing.Union[str, bool, typing.Iterable] = True
    max_request_size: int = int(1e+9)
    compress: bool = True
    log_file: typing.Optional[pathlib.Path] = None
    logging_level: typing.Optional["LoggingLevel"] = "INFO"
    logger: typing.Optional["Logger"] = None
    server_header: str = "nasse/{version} ({name})"
    sanitize_user_input: bool = True
    base_dir: pathlib.Path = pathlib.Path().resolve().absolute()
