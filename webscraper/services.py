import asyncio
import aiohttp
import async_timeout

from .models import Channel, Entry


class AioHttpScraper:
    def __init__(self):
        pass

    def run(self):
        channels = Channel.objects.enabled()
        entries_processed = 0
        for channel in channels:
            entries_processed += channel.entry_set.count()

        return len(channels), entries_processed


class URLTracker:

    """Keeps track of processed URLs"""

    def __init__(self, channel):
        self.channel = channel

    def track(self, new_urls):
        urls_to_ids = self.get_current_urls_to_ids()
        add_urls, remove_urls = list_diff(urls_to_ids.keys(), new_urls)
        ids_to_remove = [urls_to_ids[url] for url in remove_urls]
        self.bulk_remove(ids_to_remove)
        return add_urls, remove_urls

    def bulk_remove(self, ids):
        Entry.objects.delete_from_channel_by_ids(self.channel, ids)

    def get_current_urls_to_ids(self):
        rows = Entry.objects.get_id_url_for_channel(self.channel)
        return {row['url']: row['id'] for row in rows}


def list_diff(old, new):
    oldset = set(old)
    newset = set(new)
    return newset - oldset, oldset - newset


class DownloadError(Exception):
    def __init__(self, *args, **kw):
        self.message = kw.get('message')

async def get(url, sess, timeout=2):
    try:
        with async_timeout.timeout(timeout):
            resp = await sess.get(url)
            resp.raise_for_status()
            body = await resp.text(errors='ignore')

    except aiohttp.client_exceptions.ClientError as e:
        message = getattr(e, 'message', 'Generic download error')
        raise DownloadError(message=message) from e

    except asyncio.TimeoutError as e:
        raise DownloadError(message='Timeout') from e

    return resp, body
