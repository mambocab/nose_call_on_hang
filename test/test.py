"""
Run with helper that loads plugin under test.
"""
from __future__ import print_function

import time
import sys
import unittest

import logging
from mock import MagicMock
from nose.plugins import PluginTester
from nose.tools import assert_false, assert_true

from nose_call_on_hang.nose_call_on_hang import CallOnHang


log = logging.getLogger(__name__)


_cached_stdout = sys.stdout


def _fresh_plugins_with_mock(timeout):
    call_on_hang_mock = MagicMock()

    plugin_under_test = CallOnHang()
    plugin_under_test.register_timeout_function(timeout, call_on_hang_mock)

    return [plugin_under_test], call_on_hang_mock


class _CallOnHangTestException(RuntimeError):
    pass


class _TestCallOnHangMixin(PluginTester, unittest.TestCase):
    timeout, wait = None, None
    activate = '--with-callonhang'

    def makeSuite(self):
        wait = self.wait

        class TestHang(unittest.TestCase):
            def runTest(self):
                log.debug('sys.stdout is the initial value: {}'.format(
                    sys.stdout is _cached_stdout))
                log.debug('sleeping {} seconds'.format(wait))

                time.sleep(wait)

        return [TestHang()]

    def test_sleep(self):
        log.debug(self.call_on_hang_mock)
        assert_true(self.nose.success)

        if self.wait > self.timeout:
            assert_true(self.call_on_hang_mock.called)
            log.debug('it was called!')
        else:
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
