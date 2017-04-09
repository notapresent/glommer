import unittest

from webscraper.futurelite import FutureLite, InvalidStateError


class BrightFutureTestCase(unittest.TestCase):

    def setUp(self):
        self.fut = FutureLite()
        self.result = object()

    def test_returns_result(self):
        self.fut.set_result(self.result)
        self.assertIs(self.fut.result(), self.result)

    def test_result_raises_if_exception_set(self):
        exc = Exception()
        self.fut.set_exception(exc)

        with self.assertRaises(type(exc)):
            self.fut.result()

    def test_set_result_raises_if_result_set(self):
        self.fut.set_result(self.result)

        with self.assertRaises(InvalidStateError):
            self.fut.set_result(self.result)

    def test_set_exception_raises_if_result_set(self):
        self.fut.set_result(self.result)

        with self.assertRaises(InvalidStateError):
            self.fut.set_exception(Exception())

    def test_set_result_raises_if_exception_set(self):
        self.fut.set_exception(Exception())

        with self.assertRaises(InvalidStateError):
            self.fut.set_result(self.result)

    def test_set_exception_raises_if_exception_set(self):
        self.fut.set_exception(Exception())

        with self.assertRaises(InvalidStateError):
            self.fut.set_exception(Exception())

    def test_result_raises_if_pending(self):
        with self.assertRaises(InvalidStateError):
            self.fut.result()
