from pathlib import Path

from nasse.utils.args import Args


class Mode:
    DEBUG = Args.exists(("-d", "--debug"))
    PRODUCTION = Args.exists(("--production"))
    FULL_DEBUG = Args.exists("--debug")


class Enums:
    class Conventions:
        HTTP_METHODS = {"GET", "HEAD", "POST", "PUT",
                        "DELETE", "CONNECT", "OPTIONS", "TRACE", "PATCH"}  # '*' is a special method including all of the methods


class General:
    NAME = "Nasse"
    HOST = "127.0.0.1"
    VERSION = "1.0"
    SANITIZE_USER_SENT = True
    BASE_DIR = Path().resolve()
    LOGGING_TIME_FORMAT = lambda time: int(time.timestamp())
    # LOGGING_TIME_FORMAT = "%Y/%m/%d, %H:%M:%S"
    # it can either be a function or a format string
    CALL_TRACE_RECEIVER = None
    WORKER_CLASS = "sync"
    SERVER_HEADER = "Nasse/{version} ({app})"
