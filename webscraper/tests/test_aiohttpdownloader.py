import asyncio
import unittest

import aiohttp
from django.test import TestCase
from vcr_unittest import VCRMixin

from webscraper.aiohttpdownloader import fetch, DownloadError, make_session


class AioHttpDownloaderTestCase(VCRMixin, TestCase):
    def setUp(self):
        super(AioHttpDownloaderTestCase, self).setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def test_fetch_downloads(self):
        async def go():
            async with aiohttp.ClientSession(loop=self.loop) as sess:
                return await fetch('http://httpbin.org/', sess)

        resp, body = self.loop.run_until_complete(go())
        self.assertIn('ENDPOINTS', body)

    def test_get_raises_on_error(self):
        async def go():
            async with aiohttp.ClientSession(loop=self.loop) as sess:
                with self.assertRaises(DownloadError):
                    await fetch('http://httpbin.org/status/404', sess)

                with self.assertRaises(DownloadError):
                    await fetch('http://some-non-existing-domaain.net', sess)

        self.loop.run_until_complete(go())

    @unittest.skip
    def test_fetch_raises_on_timeout(self):
        self.vcr_enabled = False
        timeout = 0.5
        url = 'http://httpbin.org/delay/{}'.format(timeout + 5)

        async def go():
            async with aiohttp.ClientSession(loop=self.loop) as sess:
                with self.assertRaises(DownloadError):
                    await fetch(url, sess, timeout=timeout)

        self.loop.run_until_complete(go())

    def test_make_session(self):
        headers = {'Boo': 'hoo'}

        async def go():
            sess = await make_session(self.loop, headers=headers)
            async with sess.get('http://httpbin.org/headers') as resp:
                text = await resp.text()
            await sess.close()
            return text

        text = self.loop.run_until_complete(go())
        self.assertIn('Boo', text)
        self.assertIn('hoo', text)
