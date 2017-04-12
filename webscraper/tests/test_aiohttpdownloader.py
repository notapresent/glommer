import os
import unittest
from functools import wraps

from vcr_unittest import VCRMixin

from webscraper.aiohttpdownloader import fetch, DownloadError, make_session, download_to_future
from webscraper.futurelite import FutureLite
from .util import AsyncioTestCase


class AioHttpDownloaderTestCase(VCRMixin, AsyncioTestCase):

    def test_fetch_downloads(self):
        coro = with_session(fetch, loop=self.loop)
        resp, body = self.loop.run_until_complete(coro('http://httpbin.org/'))
        self.assertEquals(resp.status, 200)
        self.assertIn('ENDPOINTS', body)

    def test_get_raises_404(self):
        coro = with_session(fetch, loop=self.loop)
        with self.assertRaises(DownloadError):
            self.loop.run_until_complete(coro('http://httpbin.org/status/404'))

    def test_get_raises_on_nx_domain(self):
        coro = with_session(fetch, loop=self.loop)
        with self.assertRaises(DownloadError):
            self.loop.run_until_complete(coro('http://some-non-existing-domaain.net'))

    def test_make_session_sets_headers(self):
        headers = {'Boo': 'hoo'}
        coro = with_session(fetch, loop=self.loop, headers=headers)
        resp, text = self.loop.run_until_complete(coro('http://httpbin.org/headers'))
        self.assertIn('"Boo": "hoo"', text)

    def test_download_to_future_sets_result(self):
        fut = FutureLite()
        coro = with_session(download_to_future, loop=self.loop)
        self.loop.run_until_complete(coro('http://httpbin.org/', fut))
        resp, text = fut.result()
        self.assertEqual(resp.status, 200)
        self.assertIn('ENDPOINTS', text)

    def test_download_to_future_sets_exception(self):
        fut = FutureLite()
        coro = with_session(download_to_future, loop=self.loop)
        self.loop.run_until_complete(coro('http://httpbin.org/status/404', fut))
        with self.assertRaises(DownloadError):
            fut.result()


class TimeoutTestCase(AsyncioTestCase):

    @unittest.skipIf('CONTINUOUS_INTEGRATION' not in os.environ, 'Slow, CI only')
    def test_make_session_sets_read_timeout(self):
        coro = with_session(fetch, loop=self.loop, timeout=1)
        with self.assertRaises(DownloadError):
            self.loop.run_until_complete(coro('http://httpbin.org/delay/5'))

    @unittest.skipIf('CONTINUOUS_INTEGRATION' not in os.environ, 'Slow, CI only')
    def test_make_session_sets_connect_timeout(self):
        coro = with_session(fetch, loop=self.loop, timeout=1)
        with self.assertRaises(DownloadError):
            # Trying to connect to non-routeable ip address
            self.loop.run_until_complete(coro('http://10.255.255.1/'))


def with_session(f, *, loop, **sess_kw):
    """Create session and call function with it passed as keyword argument"""
    @wraps(f)
    async def wrapper(*args, **kw):
        session = make_session(loop=loop, **sess_kw)
        async with session:
            return await f(*args, **kw, session=session)

    return wrapper
