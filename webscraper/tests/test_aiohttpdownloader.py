from functools import wraps
import asyncio
import os
import unittest

from vcr_unittest import VCRMixin

from webscraper.aiohttpdownloader import fetch, DownloadError, make_session, download_to_future
from webscraper.futurelite import FutureLite


class AsyncioTestCase(unittest.TestCase):
    def setUp(self):
        super(AsyncioTestCase, self).setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()
        super(AsyncioTestCase, self).tearDown()


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
    def test_make_session_sets_timeout(self):
        coro = with_session(fetch, loop=self.loop, timeout=1)
        with self.assertRaises(DownloadError):
            self.loop.run_until_complete(coro('http://httpbin.org/delay/5'))


def with_session(f, *, loop, **sess_kw):
    """Create session and call function with it passed as keyword argument"""
    @wraps(f)
    async def wrapper(*args, **kw):
        session = await make_session(loop=loop, **sess_kw)
        with session:
            return await f(*args, **kw, session=session)

    return wrapper
