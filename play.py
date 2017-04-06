import os
import sys

import django

import asyncio


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glommer.settings')
sys.path.append(os.path.dirname(__file__))
django.setup()

from webscraper.models import Channel

from webscraper.aiohttpdownloader import Downloader, DownloadError
from webscraper.services import URLTracker
from webscraper.insbuffer import InsertBuffer
from webscraper.processing import process_entry, parse_channel, ParseError
from webscraper.extractors import make_entry_extractor


PROD_POOL_SIZE = 2
CONS_POOL_SIZE = 32


async def produce_task(channels, queue, downloader):

    """Produces tasks from channels"""

    for chan in channels:
        if chan is None:
            await queue.put(chan)
            continue

        try:
            resp, html = await downloader.get(chan.url)
            entries = parse_channel(chan, html)

        except (DownloadError, ParseError) as e:
            pass    # TODO handle errors

        else:
            ut = URLTracker(chan)
            entries = ut.track(entries)
            print('C', chan.id, chan.title, '-', len(entries), ' new entries')
            for e in entries:
                e.channel = chan
                await queue.put(e)


async def consume_task(queue, downloader, insbuffer, multiextractor):
    """Process and save entries """
    while True:
        entry = await queue.get()

        if not entry:
            break

        try:
            resp, html = await downloader.get(entry.url)

            if entry.url != resp.url:
                entry.final_url = resp.url

            entry = process_entry(entry, html, multiextractor)
            # entry.status = Entry.ST_OK if entry.items else Entry.ST_WARNING

        except DownloadError as e:
            pass    # entry.status = Entry.ST_WARNING

        except ParseError as e:
            pass    # entry.status = Entry.ST_ERROR

        finally:
            insbuffer.add(entry)


def make_workers(channels, queue, downloader, insbuffer):
    entry_extractor = make_entry_extractor()
    coros = []
    channels = list(channels)
    channels.extend([None] * CONS_POOL_SIZE)    # Send None to consumers to signal shutdown

    for i in range(PROD_POOL_SIZE):
        slice = channels[i::PROD_POOL_SIZE]
        coros.append(produce_task(slice, queue, downloader))

    for i in range(CONS_POOL_SIZE):
        coros.append(consume_task(queue, downloader, insbuffer, entry_extractor))

    return coros


def scrape(loop, channels, queue, downloader):
    buf = InsertBuffer(100)
    coros = make_workers(channels, queue, downloader, buf)
    try:
        loop.run_until_complete(asyncio.gather(*coros))

    finally:
        buf.flush()


def main():
    channels = Channel.objects.enabled()
    loop = asyncio.get_event_loop()
    dl = Downloader(loop=loop)
    queue = asyncio.Queue(CONS_POOL_SIZE * 2, loop=loop)
    try:
        scrape(loop, channels, queue, dl)
    finally:
        loop.run_until_complete(dl.teardown())

if __name__ == '__main__':
    main()

