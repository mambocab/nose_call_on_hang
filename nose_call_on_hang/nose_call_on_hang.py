import logging
import sys
import threading

from nose.plugins import Plugin

log = logging.getLogger(__name__)


class _WrappedWriter(object):
    def __init__(self, wrapped_file, pre_write_func):
        self._func = pre_write_func
        self._file = wrapped_file

    def write(self, *args, **kwargs):
        self._func(*args, **kwargs)
        self._file.write(*args, **kwargs)

    def __getattr__(self, attr):
        return getattr(self._file, attr)


class CallOnHang(Plugin):
    enabled = False
    score = 2000  # run before all builtin plugins

    def __init__(self, timers=None):
        super(CallOnHang, self).__init__()
        self._timers = [] if timers is None else timers

    def register_timer(self, timer):
        self._timers.append(timer)

    def register_timeout_function(self, timeout, function):
        self.register_timer(threading.Timer(timeout, function))

    @property
    def timers(self):
        """
        Get a tuple of the timers set for this plugin.
        """
        return tuple(self._timers)

    def begin(self):
        log.debug('Patching stdout with wrapper object')
        self._cached_stdout = sys.stdout
        sys.stdout = _WrappedWriter(wrapped_file=sys.stdout,
                                    pre_write_func=self._reset_timer)

    def finalize(self):
        log.debug('Restoring original stdout to sys.stdout')
        self._cancel_timers()
        sys.stdout = self._cached_stdout

    def beforeTest(self):
        self._reset_timers()

    def _cancel_timers(self):
        for t in self.timers:
            t.cancel()

    def _start_timers(self):
        for t in self.timers:
            t.start()

    def _restart_timers(self):
        for t in self.timers:
            t.cancel()
            t.start()
