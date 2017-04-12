import asyncio
from collections import deque
from unittest.mock import Mock

from django.test import TestCase

from webscraper.aioscraper import AioScraper, entry_worker
from .util import AsyncioTestCase


class AioScraperTestCase(AsyncioTestCase, TestCase):

    def setUp(self):
        super(AioScraperTestCase, self).setUp()

        self.entry_queue = asyncio.LifoQueue()
        self.channel_queue = deque()
        # self.loop.run_until_complete(self.init_queue())
        self.buf = Mock()
        # self.sess = SessionStub()
        self.extr = Mock()
        self.extr.extract.return_value = {}

    def test_run_flushes_buffer(self):
        s = AioScraper(loop=self.loop, insert_buffer=self.buf, entry_queue=self.entry_queue, entry_extractor=self.extr)
        s.run([])
        self.assertEquals(self.buf.flush.call_count, 1)


class EntryWorkerTestCase(AsyncioTestCase):

    def setUp(self):
        super(EntryWorkerTestCase, self).setUp()

        self.queue = asyncio.LifoQueue()
        self.loop.run_until_complete(self.init_queue())
        self.buf = set()    # Having add() method is enough
        self.sess = SessionStub()
        self.extr = Mock()
        self.extr.extract.return_value = {}

    async def init_queue(self):
        await self.queue.put(None)

    def test_exits_if_gets_none_from_queue(self):
        coro = entry_worker(0, self.queue, self.sess, self.buf, self.extr)
        self.loop.run_until_complete(coro)
        self.assertEquals(self.queue.qsize(), 0)

    def test_adds_entry_to_buffer(self):

        async def go(entry):
            await self.queue.put(entry)
            await entry_worker(0, self.queue, self.sess, self.buf, self.extr)

        entry = Mock()

        self.loop.run_until_complete(go(entry))
        self.assertEquals(self.buf, {entry})

    def test_uses_session_and_extractor(self):

        async def go(entry):
            await self.queue.put(entry)
            await entry_worker(0, self.queue, self.sess, self.buf, self.extr)

        entry = Mock()
        self.loop.run_until_complete(go(entry))

        self.assertEquals(len(self.sess.calls), 1)
        self.extr.extract.assert_called_once_with(self.sess._response._rv)


class SessionStub:

    def __init__(self, response=None):
        self.calls = []
        self._response = response or ResponseStub('http://host.com/', '<html></html>')

    def set_response(self, resp):
        self._response = resp

    def get(self, url, **kw):
        self.calls.append((url, kw))
        return self._response

    async def __aenter__(self):
        print('SessionStub aenter')
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print('SessionStub aexit')
        pass


class ResponseStub:

    def __init__(self, url, rv):
        self.url = url
        self._rv = rv

    async def text(self, *args, **kw):
        if issubclass(type(self._rv), Exception):
            raise self._rv
        else:
            return self._rv

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def raise_for_status(self):
        pass
