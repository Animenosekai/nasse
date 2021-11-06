import datetime
import inspect
import linecache

import flask
from nasse import config

RECORDING = False
LOG_STACK = []
CALL_STACK = []


class Colors:
    normal = '\033[0m'
    grey = '\033[90m'
    red = '\033[91m'
    green = '\033[92m'
    blue = '\033[94m'
    cyan = '\033[96m'
    white = '\033[97m'
    yellow = '\033[93m'
    magenta = '\033[95m'

    _colors = {normal, grey, red, green, blue, cyan, white, yellow, magenta}


class LogLevel():
    def __init__(self, level: str, template: str, debug: bool = False) -> None:
        self.level = str(level)
        self.template = str(template)
        self.debug = bool(debug)

        self._draw_time = "{time}" in self.template
        self._draw_name = "{name}" in self.template
        self._draw_step = "{step}" in self.template
        self._draw_message = "{message}" in self.template

    def __repr__(self) -> str:
        return "<LogLevel: {level}>".format(level=self.level)


class LogLevels:
    INFO = LogLevel(level="Info", template=Colors.grey +
                    "{time}｜" + Colors.normal + "[INFO] ({name}) [{step}] {message}")
    DEBUG = LogLevel(debug=True, level="Debug", template=Colors.grey +
                     "{time}｜" + Colors.normal + "[DEBUG] ({name}) [{step}] {message}")
    WARNING = LogLevel(level="Warning", template=Colors.grey +
                       "{time}｜" + Colors.normal + "[WARNING] ({name}) [{step}] " + Colors.yellow + "{message}" + Colors.normal)
    ERROR = LogLevel(level="Error", template=Colors.grey +
                     "{time}｜" + Colors.normal + "[ERROR] ({name}) [{step}] " + Colors.red + "!! {message} !!" + Colors.normal)

    def __repr__(self) -> str:
        return "<LogLevels Container>"


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


def add_to_call_stack(frame, event, arg):
    """
    Internal function to add a call to the call stack
    """
    if RECORDING and event == "call":
        if config.Mode.FULL_DEBUG:
            CALL_STACK.append(StackFrame(frame))
        elif frame.f_code.co_filename.startswith(str(config.General.BASE_DIR)):
            CALL_STACK.append(StackFrame(frame))
    return None


def clear_log():
    try:
        name = flask.g.request.app.name
    except Exception:
        name = config.General.NAME
    try:
        app_id = flask.g.request.app.id
    except Exception:
        app_id = "".join(l for l in str(name) if l.isalpha()
                         or l.isdecimal()).lower()
    with open(config.General.BASE_DIR / "{id}.nasse.log".format(id=app_id), "w", encoding="utf8") as out:
        out.write("-- {name} DEBUG LOG --\n\n".format(name=str(name).upper()))


def write_log(new_line: str):
    """Writing out the log, wether it's to the log stack or the log file"""
    #new_line = str(new_line).replace("\n", " ")
    new_line = str(new_line)
    for color in Colors._colors:
        new_line = new_line.replace(color, "")
    if RECORDING:
        LOG_STACK.append(new_line)
    if config.Mode.DEBUG:
        try:
            name = flask.g.request.app.name
        except Exception:
            name = config.General.NAME
        try:
            app_id = flask.g.request.app.id
        except Exception:
            app_id = "".join(l for l in str(
                name) if l.isalpha() or l.isdecimal()).lower()
        with open(config.General.BASE_DIR / "{id}.nasse.log".format(id=app_id), "a", encoding="utf8") as out:
            out.write(str(new_line) + "\n")


def caller_name(skip: int = 2):
    """
    https://stackoverflow.com/a/9812105/11557354
       Get a name of a caller in the format module.class.method

       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.

       An empty string is returned if skipped levels exceed stack height
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


def log(message: str = "Log", level: LogLevel = LogLevels.DEBUG, step: str = None):
    if config.Mode.PRODUCTION:
        return
    now = datetime.datetime.now()
    write_log("{time}｜[{level}] [{step}] {message}".format(time=now.timestamp(), level=level.level.upper(), step=(
        step if step is not None else (caller_name() if config.Mode.DEBUG else 'app')), message=message))

    if not level.debug or config.Mode.DEBUG:
        formatting = {}
        if level._draw_time:
            formatting["time"] = config.General.LOGGING_TIME_FORMAT(now) if callable(
                config.General.LOGGING_TIME_FORMAT) else now.strftime(str(config.General.LOGGING_TIME_FORMAT))
        if level._draw_step:
            formatting["step"] = step if step is not None else (
                caller_name() if config.Mode.DEBUG else 'Nasse App')
        if level._draw_name:
            try:
                name = flask.g.request.app.name
            except Exception:
                name = config.General.NAME
            formatting["name"] = name
        if level._draw_message:
            formatting["message"] = message

        print(level.template.format(**formatting))


class Record():
    _call_stack = []
    _log_stack = []

    @property
    def CALL_STACK(self):
        if RECORDING:
            return CALL_STACK.copy()
        return self._call_stack.copy()

    @property
    def LOG_STACK(self):
        if RECORDING:
            return LOG_STACK.copy()
        return self._log_stack.copy()

    def start(self):
        global RECORDING
        CALL_STACK.clear()
        LOG_STACK.clear()
        RECORDING = True

    def stop(self):
        global RECORDING
        self._call_stack = CALL_STACK.copy()
        self._log_stack = LOG_STACK.copy()
        RECORDING = False
        CALL_STACK.clear()
        LOG_STACK.clear()
        return self._call_stack, self._log_stack

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.stop()
