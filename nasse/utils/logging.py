import dataclasses
import datetime
import enum
import inspect
import linecache
import os
import pathlib
import threading
import typing


class LoggingLevel(enum.Enum):
    ERROR = 1
    WARNING = 2
    INFO = 3
    DEBUG = 4
    HIDDEN = 999


@dataclasses.dataclass
class Record:
    def __post_init__(self):
        self.time = datetime.datetime.now()

    level: LoggingLevel
    msg: str


class Colors(enum.Enum):
    NORMAL = '\033[0m'
    GREY = '\033[90m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'


class Logger:
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

    def __init__(self, config: "config.NasseConfig" = None, file_output: pathlib.Path = None) -> None:
        self.config = config
        if not self.config:
            from nasse.config import NasseConfig

            class NewConfig(NasseConfig):
                def verify_logger(self):
                    return

            self.config = NewConfig()
        self.recording = False
        self.record = []

        if file_output:
            self.file_output = pathlib.Path(file_output)
            with open(self.file_output, "a") as f:
                WIDTH = 32
                MESSAGE = "LOG START"
                padding = WIDTH - len(MESSAGE) // 2
                f.write(("=" * padding) + MESSAGE + ("=" * padding) + "\n")
        else:
            self.file_output = None

    def log(self, *msg, level: LoggingLevel = LoggingLevel.INFO, end: str = "\n", sep: str = " "):
        """
        Logging the given message to the console.
        """
        if level.value > self.config.logging_level.value:
            return

        result = str(sep).join(msg)

        formatter = {
            # colors
            "normal": Colors.NORMAL.value,
            "grey": Colors.GREY.value,
            "gray": Colors.GREY.value,
            "red": Colors.RED.value,
            "green": Colors.GREEN.value,
            "blue": Colors.BLUE.value,
            "cyan": Colors.CYAN.value,
            "turquoise": Colors.CYAN.value,
            "white": Colors.WHITE.value,
            "yellow": Colors.YELLOW.value,
            "purple": Colors.MAGENTA.value,
            "pink": Colors.MAGENTA.value,
            "magenta": Colors.MAGENTA.value,
            "level": level.name,
            "app": self.config.app,
            "host": self.config.host,
            "port": self.config.port,
            "debug": self.config.debug,
            "base_dir": self.config.base_dir
        }
        time = datetime.datetime.now()
        if "{time}" in result:  # current time
            formatter["time"] = self.TIME_FORMAT(time) if callable(self.TIME_FORMAT) else time.strftime(self.TIME_FORMAT)
        if "{caller}" in result:  # caller function
            formatter["caller"] = caller_name()
        if "{thread}" in result:  # thread id
            formatter["thread"] = threading.get_ident()
        if "{pid}" in result:  # process id
            formatter["pid"] = os.getpid()
        if "{cwd}" in result:  # current working directory
            formatter["cwd"] = os.getcwd()

        result = result.format(**formatter)

        record_output = result
        for element in Colors:
            # removing the colors for any file or recording output
            record_output = record_output.replace(element.value, "")

        if self.recording:
            self.record.append(Record(level=level, msg=record_output))

        if self.file_output:
            with open(self.file_output, "a") as f:
                f.write("[{level}] ({app}) - {time} - {msg}\n".format(
                    level=level.name,
                    app=self.config.app,
                    time=int(time.timestamp()),
                    msg=record_output
                ))

        formatter["message"] = result
        template = self.TEMPLATES.get(level, "{message}")

        if "{time}" in template:  # current time
            formatter["time"] = self.TIME_FORMAT(time) if callable(self.TIME_FORMAT) else time.strftime(self.TIME_FORMAT)
        if "{caller}" in template:  # caller function
            formatter["caller"] = caller_name()
        if "{thread}" in template:  # thread id
            formatter["thread"] = threading.get_ident()
        if "{pid}" in template:  # process id
            formatter["pid"] = os.getpid()
        if "{cwd}" in template:  # current working directory
            formatter["cwd"] = os.getcwd()

        result = template.format(**formatter)

        print(result, end=str(end))

    def info(self, *msg, **kwargs):
        """
        Logs the given message with the `INFO` level
        """
        self.log(*msg, level=LoggingLevel.INFO, **kwargs)

    # aliasing `info`
    print = info

    def debug(self, *msg, **kwargs):
        """
        Logs the given message with the `DEBUG` level
        """
        self.log(*msg, level=LoggingLevel.DEBUG, **kwargs)

    def warning(self, *msg, **kwargs):
        """
        Logs the given message with the `WARNING` level
        """
        self.log(*msg, level=LoggingLevel.WARNING, **kwargs)

    warn = warning

    def error(self, *msg, **kwargs):
        """
        Logs the given message with the `ERROR` level
        """
        self.log(*msg, level=LoggingLevel.ERROR, **kwargs)

    def hidden(self, *msg, **kwargs):
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


RECORDING = False
CALL_STACK = []


class StackFrame():
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
            "calledBy": "<{name}>, in {filename} at line {line_number}".format(name=self.back_frame.f_code.co_name, filename=self.back_frame.f_code.co_filename, line_number=self.back_frame.f_code.co_firstlineno)
        }


class CallStackRecorder:
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
        if RECORDING and event == "call" and frame.f_code.co_filename.startswith(config.base_dir):
            CALL_STACK.append(StackFrame(frame))
        return None
    return add_to_call_stack


def caller_name(skip: int = 2):
    """
    Get a name of a caller in the format module.class.method

    `skip` specifies how many levels of stack to skip while getting caller
    name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

    An empty string is returned if skipped levels exceed stack height

    Note: https://stackoverflow.com/a/9812105/11557354       
    """
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
        return ''
    parentframe = stack[start][0]
    name = []
    module = inspect.getmodule(parentframe)
    if module:
        name.append(module.__name__)
    if 'self' in parentframe.f_locals:
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append(codename)  # function or a method
    del parentframe, stack
    return ".".join(name)


logger = Logger()
