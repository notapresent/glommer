"""Task scheduling/queueing and scrape flow control"""
import asyncio
import logging
from collections import deque

from .aiohttpdownloader import make_session, download_to_future
from .futurelite import FutureLite
from .insbuffer import InsertBuffer
from .processing import process_channel, process_entry

# Default values
CHANNEL_POOL_SIZE = 2
ENTRY_POOL_SIZE = 32
INSERT_BUFFER_SIZE = 150

logger = logging.getLogger(__name__)


class AioScraper:
    """Holds scrape state, like queues, client sessions etc"""

    def __init__(self, loop, insert_buffer, entry_queue):
        self._loop = loop
        self._insert_buffer = insert_buffer
        self._entry_queue = entry_queue
        self._channel_queue = None

    def run(self, channels):
        self._channel_queue = deque(channels)
        self._channel_queue.extend([None] * CHANNEL_POOL_SIZE)   # Signal channel workers to shut down

        try:
            self._loop.run_until_complete(self._run())

        finally:
            self._insert_buffer.flush()

    async def _run(self):
        self._session = make_session(self._loop)
        workers = self.make_channel_workers() + self.make_entry_workers()

        async with self._session:
            await asyncio.gather(*workers, loop=self._loop)

    def make_channel_workers(self):
        args = (self._channel_queue, self._entry_queue, self._session)
        return [channel_worker(i, *args) for i in range(CHANNEL_POOL_SIZE)]

    def make_entry_workers(self):
        args = (self._entry_queue, self._session, self._insert_buffer)
        return [entry_worker(i, *args) for i in range(ENTRY_POOL_SIZE)]


def scrape(channels):
    loop = asyncio.get_event_loop()
    buf = InsertBuffer(INSERT_BUFFER_SIZE)
    eq = asyncio.Queue(ENTRY_POOL_SIZE * 2, loop=loop)
    scraper = AioScraper(loop=loop, insert_buffer=buf, entry_queue=eq)
    try:
        scraper.run(channels)

    finally:
        loop.close()


async def channel_worker(worker_no, channel_queue, entry_queue, session):
    logger.info('Channel worker #%d started' % worker_no)

    while True:
        channel = channel_queue.popleft()

        if channel is None:
            break

        fut = FutureLite()
        await download_to_future(channel.url, fut, session=session)
        new_entries = process_channel(channel, fut)
        channel.save()

        for entry in new_entries:
            await entry_queue.put(entry)

    if not channel_queue:   # this is the last channel worker left
        logger.info('Channel worker #%d signaling entry workers to shut down' % worker_no)

        for _ in range(ENTRY_POOL_SIZE):
            await entry_queue.put(None)

    logger.info('Terminating channel worker #%d' % worker_no)


async def entry_worker(worker_no, entry_queue, session, buffer):
    logger.info('Entry worker #%d started' % worker_no)

    while True:
        entry = await entry_queue.get()

        if entry is None:
            break

        lfut = FutureLite()
        await asyncio.shield(download_to_future(entry.url, lfut, session=session))
        process_entry(entry, lfut)

        buffer.add(entry)

    logger.info('Entry worker #%d got None, terminating' % worker_no)
