from __future__ import print_function

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
        self._func()
        self._file.write(*args, **kwargs)

    def __getattr__(self, attr):
        return getattr(self._file, attr)


class CallOnHang(Plugin):
    enabled = False
    score = 2000  # run before all builtin plugins

    def __init__(self, timers=None, enabled=False):
        super(CallOnHang, self).__init__()
        self._timers = [] if timers is None else list(timers)
        self.enabled = enabled

    def register_timer(self, timer):
        self._timers.append(timer)

    def register_timeout_function(self, timeout, function):
        self.register_timer(threading.Timer(timeout, function))

    @property
    def timers(self):
        """
        Iterate over the timers registered with this plugin.
        """
        for t in self._timers:
            yield t

    def begin(self):
        log.debug('Patching stdout with wrapper object')
        self._cached_stdout = sys.stdout
        sys.stdout = _WrappedWriter(wrapped_file=sys.stdout,
                                    pre_write_func=self._restart_timers)

    def finalize(self, result):
        log.debug('Restoring original stdout to sys.stdout')
        self._cancel_timers()
        sys.stdout = self._cached_stdout

    def beforeTest(self, test):
        self._restart_timers()

    def _cancel_timers(self):
        for t in self.timers:
            t.cancel()

    def _start_timers(self):
        for t in self.timers:
            t.start()

    def _restart_timers(self):
        log.debug('starting fresh timers')
        self._cancel_timers()
        self._timers = [threading.Timer(interval=t.interval,
                                        function=t.function,
                                        args=t.args,
                                        kwargs=t.kwargs)
                        for t in self.timers]
        self._start_timers()
