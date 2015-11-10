"""
Run with helper that loads plugin under test.
"""
from __future__ import print_function

import logging
import sys
import time
import unittest

from mock import MagicMock
from nose.plugins import PluginTester
from nose.tools import assert_false, assert_is, assert_is_not, assert_true
from nose_call_on_hang.nose_call_on_hang import CallOnHang

log = logging.getLogger(__name__)


_cached_stdout = sys.stdout


def _fresh_plugins_with_mock(timeout):
    call_on_hang_mock = MagicMock()

    plugin_under_test = CallOnHang()
    plugin_under_test.register_timeout_function(timeout, call_on_hang_mock)

    return [plugin_under_test], call_on_hang_mock


class _TestCallOnHangMixin(PluginTester, unittest.TestCase):
    timeout, wait = None, None
    activate = '--with-callonhang'

    def setUp(self):
        self.call_on_hang_mock.reset_mock()
        super(_TestCallOnHangMixin, self).setUp()

    def makeSuite(self):
        wait = self.wait

        class TestHang(unittest.TestCase):
            def runTest(self):
                log.debug('sys.stdout is the initial value: {}'.format(
                    sys.stdout is _cached_stdout))
                assert_is_not(sys.stdout, _cached_stdout)  # sys.stdout should be replaced

                log.debug('sleeping {} seconds'.format(wait))
                time.sleep(wait)

        return [TestHang()]

    def test_sleep(self):
        log.debug(self.call_on_hang_mock)
        assert_true(self.nose.success)  # all the tests should pass
        assert_true(self.output)  # output shouldn't be empty, i.e. redirection should still be working
        assert_is(sys.stdout, _cached_stdout)  # sys.stdout should be restored by now

        if self.wait > self.timeout:
            # if the background timer's timeout is longer than how long the test will wait,
            # the mock should have been called
            assert_false(self.call_on_hang_mock.called)
            log.debug('it was called!')
        else:
            # otherwise, it shouldn't have been called
            assert_false(self.call_on_hang_mock.called)
            log.debug('not called!')


class TestCallSleep2Seconds(_TestCallOnHangMixin):
    timeout, wait = 5, 2
    plugins, call_on_hang_mock = _fresh_plugins_with_mock(timeout)


class TestCallSleep7Seconds(_TestCallOnHangMixin):
    timeout, wait = 5, 7
    plugins, call_on_hang_mock = _fresh_plugins_with_mock(timeout)


class TestCallSleep2SecondsTwice(_TestCallOnHangMixin):
    timeout, wait = 5, 2
    plugins, call_on_hang_mock = _fresh_plugins_with_mock(timeout)
    test_sleep_again = _TestCallOnHangMixin.test_sleep


class TestCallSleep7SecondsTwice(_TestCallOnHangMixin):
    timeout, wait = 5, 7
    plugins, call_on_hang_mock = _fresh_plugins_with_mock(timeout)
    test_sleep_again = _TestCallOnHangMixin.test_sleep
