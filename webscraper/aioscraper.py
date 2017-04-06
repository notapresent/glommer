import asyncio

from .models import Channel, Entry
from .aiohttpdownloader import DownloadError


class AioHttpScraper:
    def __init__(self, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._queue = asyncio.Queue(loop=self._loop)

    def run(self):
        channels = Channel.objects.enabled()
        entries_processed = 0
        for channel in channels:
            entries_processed += channel.entry_set.count()

        return len(channels), entries_processed



def process_channel(channel, fut):
    try:
        response, html = fut.result()
        entries = parse_channel(channel, html)
    except DownloadError as e:
        pass    # channel.status = Channel.ST_ERROR

    except ParseError as e:
        pass    # channel.status = Channel.ST_E

    else:
        # channel.status = Channel.ST_OK
        pass

    finally:
        channel.save()

    return entries


class ParseError(Exception):
    pass


def parse_channel(channel, html):
    pass


def process_entry(entry, fut):
    try:
        resp, html = fut.result()
        entry.final_url = resp.url
        items = parse_entry(entry, html)

    except DownloadError as e:
        pass    # entry.status = Entry.ST_ERROR

    except ParseError as e:
        pass    # entry.status = Entry.ST_ERROR

    else:
        entry.items = items
        # entry.status = Entry.ST_OK if items else Entry.ST_WARN

    return entry


def parse_entry(entry, html):
    pass

