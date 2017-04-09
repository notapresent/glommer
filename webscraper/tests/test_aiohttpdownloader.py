import os
import asyncio
import unittest

import aiohttp
import async_timeout

from vcr_unittest import VCRTestCase

from webscraper.aiohttpdownloader import fetch, DownloadError, make_session


class AioHttpDownloaderTestCase(VCRTestCase):

    def setUp(self):
        super(AioHttpDownloaderTestCase, self).setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_fetch_downloads(self):
        coro = make_session_and_fetch(self.loop, 'http://httpbin.org/')
        resp, body = self.loop.run_until_complete(coro)
        self.assertIn('ENDPOINTS', body)

    def test_get_raises_on_404(self):
        coro = make_session_and_fetch(self.loop, 'http://httpbin.org/status/404')
        with self.assertRaises(DownloadError):
            self.loop.run_until_complete(coro)

    def test_get_raises_on_nx_domain(self):
        coro = make_session_and_fetch(self.loop, 'http://some-non-existing-domaain.net')
        with self.assertRaises(DownloadError):
            self.loop.run_until_complete(coro)

    def test_make_session_returns_working_session(self):
        coro = make_session_and_get(self.loop, 'http://httpbin.org/headers')
        resp, text = self.loop.run_until_complete(coro)
        self.assertEquals(resp.status, 200)
        self.assertIn('headers', text)

    def test_make_session_sets_headers(self):
        headers = {'Boo': 'hoo'}
        coro = make_session_and_get(self.loop, 'http://httpbin.org/headers', headers=headers)
        resp, text = self.loop.run_until_complete(coro)
        self.assertIn('"Boo": "hoo"', text)


class TimeoutTestCase(unittest.TestCase):
    def setUp(self):
        super(TimeoutTestCase, self).setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    @unittest.skipIf('CONTINUOUS_INTEGRATION' not in os.environ, 'CI only')
    def test_timeout(self):
        coro = make_session_and_fetch(self.loop, 'http://httpbin.org/delay/5', timeout=1)
        with self.assertRaises(DownloadError):
            self.loop.run_until_complete(coro)

    def tearDown(self):
        self.loop.close()


async def make_session_and_get(loop, url, *args, **kw):
    sess = await make_session(loop=loop, *args, **kw)
    async with sess, sess.get(url) as resp:
        text = await resp.text()
    return resp, text


async def make_session_and_fetch(loop, url, *args, **kw):
    sess = await make_session(loop=loop, *args, **kw)
    async with sess:
        resp, text = await fetch(url, sess)
    return resp, text