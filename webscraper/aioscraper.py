"""Task scheduling/queueing and scrape flow control"""
import asyncio
import logging
from collections import deque

import async_timeout


from .futurelite import FutureLite
from .aiohttpdownloader import DownloadError, fetch, make_session
from .processing import process_channel, process_entry, make_entry_extractor
from .insbuffer import InsertBuffer


# Default values
CHANNEL_POOL_SIZE = 2
ENTRY_POOL_SIZE = 32
INSERT_BUFFER_SIZE = 150
GLOBAL_TIMEOUT = 60 * 5

logger = logging.getLogger(__name__)


class AioScraper:
    """Holds scrape state, like queues, client sessions etc"""

    def __init__(self, loop=None, session=None, insert_buffer=None, entry_queue=None, entry_extractor=None):
        self._loop = loop
        self._insert_buffer = insert_buffer
        self._entry_queue = entry_queue
        self._entry_extractor = entry_extractor
        self._channel_queue = None

    def run(self, channels):
        self._channel_queue = deque(channels)
        self._channel_queue .extend([None] * ENTRY_POOL_SIZE)   # Signal entry workers to shut down
        try:
            self._loop.run_until_complete(self._run())
        finally:
            self._insert_buffer.flush()

    async def _run(self):
        self._session = await make_session(self._loop)
        workers = self.make_channel_workers() + self.make_entry_workers()

        with async_timeout.timeout(GLOBAL_TIMEOUT):
            async with self._session:
                await asyncio.gather(loop=self._loop, *workers)

    def make_channel_workers(self):
        args = (self._channel_queue, self._entry_queue, self._session)
        return [channel_worker(*args) for _ in range(CHANNEL_POOL_SIZE)]

    def make_entry_workers(self):
        args = (self._entry_queue, self._session, self._insert_buffer, self._entry_extractor)
        return [entry_worker(*args) for _ in range(ENTRY_POOL_SIZE)]


def scrape(channels):
    loop = asyncio.get_event_loop()
    buf = InsertBuffer(INSERT_BUFFER_SIZE)
    eq = asyncio.Queue(ENTRY_POOL_SIZE * 2, loop=loop)
    ee = make_entry_extractor()
    scraper = AioScraper(loop=loop, insert_buffer=buf, entry_queue=eq, entry_extractor=ee)
    try:
        scraper.run(channels)
    finally:
        loop.close()


async def channel_worker(channel_queue, entry_queue, session):
    while channel_queue:
        channel = channel_queue.popleft()

        if channel is None:
            await entry_queue.put(None)
            continue

        fut = FutureLite()
        await download_to_future(fut, session, channel.url)
        new_entries = process_channel(channel, fut)

        for entry in new_entries:
            await entry_queue.put(entry)


async def entry_worker(entry_queue, session, buffer, entry_extractor):
    while True:
        entry = await entry_queue.get()

        if entry is None:
            break

        fut = FutureLite()
        await download_to_future(fut, session, entry.url)
        process_entry(entry, fut, entry_extractor)
        buffer.add(entry)


async def download_to_future(fut, session, url):
    """Fetch and store result or exception in future"""
    try:
        resp, html = await fetch(url, session)
        fut.set_result((resp, html))

    except (DownloadError) as e:
        fut.set_exception(e)
