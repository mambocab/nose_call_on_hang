from __future__ import print_function

import logging
import sys
import threading

from nose.plugins import Plugin

log = logging.getLogger(__name__)


class _WrappedWriter(object):
    """
    An object that wraps a file (or anything with a write method) and
    intercepts calls to write, first calling a function defined at object
    initialization.
    """
    def __init__(self, wrapped_file, pre_write_func):
        """
        Create a _WrappedWriter. Takes a file-like object (or anything with a
        write method) and a callable. It should be possible to call the
        callable with no arguments.
        """
        self._func = pre_write_func
        self._file = wrapped_file

    def write(self, *args, **kwargs):
        """
        Calls the registered callable, then calls write on the wrapped object,
        passing all arguments.
        """
        self._func()
        self._file.write(*args, **kwargs)

    # just get attributes other than write from the wrapped object
    def __getattr__(self, attr):
        return getattr(self._file, attr)


class CallOnHang(Plugin):
    """
    A plugin that maintains a number of timers that run in a separate thread
    while tests run in the main thread, and resets them whenever the test
    writes to stdout. The timers start when nose starts running a given test
    (when it calls plugins' beforeTest method). If the timers time out because
    nothing was printed to stdout, they will call the function they were
    instantiated with, then be reset again when something is written to stdout
    again.

    Inherits from nose.plugins.Plugin.

    The purpose of this plugin is to detect when a test is hung, using printing
    to stdout as a proxy for not being hung. The problem that motivated writing
    this plugin was a problem running the the Cassandra dtest suite in CI.
    Sometimes tests would hang, and after 30 minutes, Jenkins would end the
    entire test run and produce no junit output. This plugin allows us to
    register a timer that fails the test after a preset timeout if there's no
    stdout, preempting Jenkins' timeout.

    Because using this plugin involves registering timers or functions with
    timeouts, this plugin doesn't provide a command-line configuration
    interface. Instead, you need to write a small Python script to configure
    the plugin and call nose programatically:

    >>> hang_plugin = CallOnHang(timers=[...], enabled=True)
    >>> # configure hang_plugin object further with timer-registration methods
    >>> nose.main(addplugins=[hang_plugin])

    By default, nose.main will use sys.argv, so running such a script can be a
    drop-in replacement for running the nosetests command.

    """
    enabled = False
    score = 2000  # run before all builtin plugins

    def __init__(self, timers=None, enabled=False):
        """
        Initialize the plugin. Optionally takes two arguments:

        - timers, an iterable of therading.Timer objects
        - enabled, a boolean used by nose to determine whether or not to use
          the plugin when running tests.

        Passing a value for enabled in __init__:

        >>> hang_plugin = CallOnHang(enabled=True)

        is equivalent to setting the enabled attribute on an instantiated
        plugin:

        >>> hang_plugin = CallOnHang()
        >>> hang_plugin.enabled = True
        """
        super(CallOnHang, self).__init__()
        self._timers = [] if timers is None else list(timers)
        self.enabled = enabled

    def register_timer(self, timer):
        """
        Register the argument timer, a threading.Timer object, as a timer to
        be run in the background while tests are run.
        """
        self._timers.append(timer)

    def register_timeout_function(self, timeout, function):
        """
        Register the argument function, a 0-argument callable, to be called
        to be called after n seconds, where n is given as the argument timeout.

        Internally, this creates a threading.Timer object with the given
        timeout and function and register it in the plugin's list of timers.
        """
        self.register_timer(threading.Timer(timeout, function))

    @property
    def timers(self):
        """
        Iterate over the timers registered with this plugin.
        """
        for t in self._timers:
            yield t

    def begin(self):
        """
        Monkeypatch sys, replacing stdout with a wrapped version that will
        restart the timers registered with this plugin. sys.stdout will be
        returned to its rightful place on the call to finalize.
        """
        log.debug('Patching stdout with wrapper object')
        self._cached_stdout = sys.stdout
        sys.stdout = _WrappedWriter(wrapped_file=sys.stdout,
                                    pre_write_func=self._restart_timers)

    def finalize(self, result):
        """
        Un-monkeypatch sys.stdout.
        """
        log.debug('Restoring original stdout to sys.stdout')
        self._cancel_timers()
        sys.stdout = self._cached_stdout

    def beforeTest(self, test):
        """
        Start or restart the timers registered with this plugin.
        """
        self._restart_timers()

    def _cancel_timers(self):
        """
        Cancel the timers registered with this plugin.
        """
        for t in self.timers:
            t.cancel()

    def _start_timers(self):
        """
        Start the timers registered with this plugin.
        """
        for t in self.timers:
            t.start()

    def _restart_timers(self):
        """
        Restart the timers registered with this plugin. Since threading.Timer
        objects can't be started more than once, the implementation here
        creates new, timer objects that behave identically to the existing
        ones. As a result, users can't depend on object identity of the members
        of timers before and after calls to this method.
        """
        log.debug('starting fresh timers')
        self._cancel_timers()
        # threading.Timer objects can't be started more than once, so for
        # each timer, create a new, functionally identical Timer.
        self._timers = [threading.Timer(interval=t.interval,
                                        function=t.function,
                                        args=t.args,
                                        kwargs=t.kwargs)
                        for t in self.timers]
        self._start_timers()
