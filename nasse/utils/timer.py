import time
import sys

if sys.version_info > (3, 7):
    process_time_ns = time.process_time_ns # novermin
else:
    process_time_ns = lambda: int(time.process_time() * 1e+9)

class Timer():
    def __init__(self) -> None:
        """
        A timer to measure performance of a piece of code

        Example
        -------
        >>> from nasse.timer import Timer
        >>> with Timer() as timer:
        ...     # do heavy stuff
        >>> timer.time
        5.628793271 # in seconds
        >>> timer.time_ns
        5628793271 # in nanoseconds
        """
        self.current_timer = process_time_ns()
        self.time_ns = 0
        self.time = 0

    def start(self):
        """
        Manually starts the timer
        """
        self.current_timer = process_time_ns()
        self.time_ns = 0
        self.time = 0

    def stop(self):
        """
        Save the current time

        Returns
        --------
            float
                The time taken between Timer.start() and now (in seconds)
        """
        self.time_ns = process_time_ns() - self.current_timer
        self.time = self.time_ns / 1e+9
        return self.time

    def __enter__(self):
        self.current_timer = process_time_ns()
        self.time_ns = 0
        self.time = 0
        return self

    def __exit__(self, type, value, traceback):
        self.time_ns = process_time_ns() - self.current_timer
        self.time = self.time_ns / 1e+9
