"""
Nasse logging utilities

Copyright
---------
Animenosekai
    Original author, MIT License
"""
import dataclasses
import datetime
import enum
import linecache
import typing

import rich.console
from nasse.utils import formatter


class LoggingLevel(enum.Enum):
    """
    A logging level
    """
    ERROR = 1
    WARNING = 2
    INFO = 3
    DEBUG = 4
    HIDDEN = 999


@dataclasses.dataclass
class Record:
    """
    Represents a record in the log stack
    """

    def __post_init__(self):
        self.time = datetime.datetime.now()

    level: LoggingLevel
    msg: str


class Logger:
    """
    A Nasse logging object, the logger used thoughout your app
    """

    TIME_FORMAT: typing.Union[str, typing.Callable[[datetime.datetime], typing.Any]] = "%Y/%m/%d, %H:%M:%S"
    # TIME_FORMAT = lambda time: int(time.timestamp())
    """
    The logging time format

    It can be either a function taking a datetime.datetime object or a string,
    which will be passed to datetime.datetime.strftime
    """

    TEMPLATES = {
        LoggingLevel.INFO: "{grey}{time} | {normal}[{level}] ({app}) {message}",
        LoggingLevel.DEBUG: "{grey}{time} | [{level}] ({app}) {message}{normal}",
        LoggingLevel.WARNING: "{grey}{time} |{normal} [{level}] ({app}) {yellow}{message}{normal}",
        LoggingLevel.ERROR: "{grey}{time} |{normal} [{level}] ({app}) {red}{message}{normal}"
    }

    def __init__(self, config: "config.NasseConfig" = None) -> None:
        self.config = config
        if not self.config:
            from nasse.config import NasseConfig

            class NewConfig(NasseConfig):
                def verify_logger(self):
                    return

            self.config = NewConfig()
        self.recording = False
        self.record = []

        self._rich_console = rich.console.Console()

        if self.config.log_file:
            self.config.log_file.parent.mkdir(parents=True, exist_ok=True)
            self.config.log_file.touch(exist_ok=True)
            with open(self.config.log_file, "a") as f:
                WIDTH = 32
                MESSAGE = "LOG START"
                padding = WIDTH - len(MESSAGE) // 2
                f.write(("=" * padding) + MESSAGE + ("=" * padding) + "\n")

    def log(self, *msg,
            level: LoggingLevel = LoggingLevel.INFO,
            end: str = "\n",
            sep: str = " ", **kwargs) -> None:
        """
        Logging the given message to the console.
        """
        if level.value > self.config.logging_level.value:
            return

        result = formatter.format(
            str(sep).join(str(m) for m in msg),
            time_format=self.TIME_FORMAT,
            config=self.config,
            level=level.name,
            **kwargs
        )

        record_output = result
        for element in formatter.Colors:
            # removing the colors for any file or recording output
            record_output = record_output.replace(element.value, "")

        if self.recording:
            self.record.append(Record(level=level, msg=record_output))

        if self.config.log_file:
            self.write_to_file(msg=record_output, level=level, **kwargs)

        template = self.TEMPLATES.get(level, "{message}")
        result = formatter.format(template, time_format=self.TIME_FORMAT, config=self.config, level=level.name, message=result, **kwargs)

        print(result, end=str(end))

    __call__ = log

    def write_to_file(self,
                      msg: str,
                      level: LoggingLevel = LoggingLevel.INFO,
                      **kwargs) -> None:
        """
        Internal function called to write to the log file
        """
        if not self.config.log_file:
            return

        self.config.log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.log_file, "a", encoding="utf-8") as f:
            f.write(formatter.format("[{level}] ({name}) - {time} - {msg}\n",
                                     time_format=lambda time: int(time.timestamp()),
                                     level=level.name,
                                     name=self.config.name,
                                     msg=msg,
                                     **kwargs))

    def info(self, *msg, **kwargs):
        """
        Logs the given message with the `INFO` level
        """
        self.log(*msg, level=LoggingLevel.INFO, **kwargs)

    # aliasing `info`
    print = info

    def debug(self, *msg, **kwargs) -> None:
        """
        Logs the given message with the `DEBUG` level
        """
        self.log(*msg, level=LoggingLevel.DEBUG, **kwargs)

    def warning(self, *msg, **kwargs) -> None:
        """
        Logs the given message with the `WARNING` level
        """
        self.log(*msg, level=LoggingLevel.WARNING, **kwargs)

    warn = warning

    def error(self, *msg, **kwargs) -> None:
        """
        Logs the given message with the `ERROR` level
        """
        self.log(*msg, level=LoggingLevel.ERROR, **kwargs)

    def hidden(self, *msg, **kwargs) -> None:
        """
        Logs the given message with the `HIDDEN` level

        It only writes to the log file and the records
        """
        self.log(*msg, level=LoggingLevel.HIDDEN, **kwargs)

    hide = hidden

    def __enter__(self):
        """
        Begins recording the output
        """
        self.recording = True
        self.record = []
        return self

    def __exit__(self, type, value, traceback):
        """
        Stops recording the output
        """
        self.recording = False

    def print_exception(self,
                        show_locals: bool = False,
                        **kwargs) -> None:
        """
        Prints the latest exception, nicely

        Parameters
        ----------
        show_locals: bool, default = False
            When enabled, shows the local variables to the console
        """
        self._rich_console.print_exception(show_locals=show_locals, **kwargs)

    exception = print_exception


RECORDING = False
CALL_STACK = []


class StackFrame:
    """
    A call stack frame
    """

    def __init__(self, frame) -> None:
        # print(dir(frame))
        # print(dir(frame.f_code))
        self.name = frame.f_code.co_name
        self.filename = frame.f_code.co_filename
        self.lineno = frame.f_lineno
        self.back_frame = frame.f_back
        self._line = None
        self._calling_line = None

    def __repr__(self) -> str:
        return "<NasseStackFrame '{name}' {filename} on {line_number}>".format(name=self.name, filename=self.filename, line_number=self.lineno)

    @property
    def line(self):
        if self._line is None:
            self._line = linecache.getline(self.filename, self.lineno)
        return self._line.strip()

    @property
    def calling_line(self):
        if self._calling_line is None:
            self._calling_line = linecache.getline(
                self.back_frame.f_code.co_filename, self.back_frame.f_lineno)
        return self._calling_line.strip()

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "filename": self.filename,
            "lineNumber": self.lineno,
            "calledBy": {
                "name": self.back_frame.f_code.co_name,
                "filename": self.back_frame.f_code.co_filename,
                "lineNumber": self.back_frame.f_code.co_firstlineno
            }
        }


class CallStackRecorder:
    """
    A call stack recorder
    """

    def __enter__(self):
        """
        Begins recording the calls
        """
        global RECORDING
        global CALL_STACK
        RECORDING = True
        CALL_STACK = []
        return self

    @property
    def recording(self):
        return RECORDING

    @property
    def call_stack(self):
        return CALL_STACK

    def __exit__(self, type, value, traceback):
        """
        Stops recording
        """
        global RECORDING
        RECORDING = False


def _generate_trace(config):
    """
    Internal function to generate a trace to record the call stack
    """
    def add_to_call_stack(frame, event, arg):
        """
        Internal function to add a call to the call stack
        """
        if RECORDING and event == "call" and frame.f_code.co_filename.startswith(str(config.base_dir)):
            CALL_STACK.append(StackFrame(frame))
        return None
    return add_to_call_stack


logger = Logger()


def log(*msg,
        level: LoggingLevel = LoggingLevel.INFO,
        end: str = "\n",
        sep: str = " ", **kwargs) -> None:
    """
    Logging the given message to the console.
    """
    logger.log(*msg, level=level, end=end, sep=sep, **kwargs)


info = log


def debug(*msg, **kwargs) -> None:
    """
    Logs the given message with the `DEBUG` level
    """
    logger.debug(*msg, **kwargs)


def warning(*msg, **kwargs) -> None:
    """
    Logs the given message with the `WARNING` level
    """
    logger.warning(*msg, **kwargs)


warn = warning


def error(*msg, **kwargs) -> None:
    """
    Logs the given message with the `ERROR` level
    """
    logger.error(*msg, **kwargs)


def hidden(*msg, **kwargs) -> None:
    """
    Logs the given message with the `HIDDEN` level

    It only writes to the log file and the records
    """
    logger.hidden(*msg, **kwargs)


hide = hidden
