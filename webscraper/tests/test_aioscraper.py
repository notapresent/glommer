import asyncio

from django.test import TestCase
from .util import AsyncioTestCase
from unittest.mock import Mock, MagicMock

from webscraper.aioscraper import AioScraper, channel_worker, entry_worker



class AioHttpScraperTestCase(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)


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
        self.extr.extract.assert_called_once_with(self.sess.text)


class SessionStub:
    def __init__(self):
        self.calls = []
        self.text = '<html></html>'
        self.response = MagicMock()
        self.response.text = self.get_text

    async def get(self, url, **kw):
        self.calls.append((url, kw))
        return self

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def get_text(self, **kw):
        return self.text
