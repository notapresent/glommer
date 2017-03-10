import asyncio
import aiohttp
import os
import hashlib
import async_timeout
from urllib.parse import urljoin

import requests
from django.conf import settings

from .extractors import DatasetExtractor
from .models import Channel, Entry

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 Glommer/1.0'
}

REQUEST_TIMEOUT = 2 # seconds


class Scraper:
    def __init__(self):
        self.session = None
        self.current_tasks = {}

    def run(self):
        loop = asyncio.get_event_loop()
        entry_num_list = loop.run_until_complete(self.task_wrapper())
        loop.close()
        print(entry_num_list)
        for r in entry_num_list:
            if isinstance(r, BaseException):
                raise r

        return len(entry_num_list), sum(entry_num_list)

    async def task_wrapper(self):
        channels = self.get_channels()
        tasks = [self.process_channel(c) for c in channels]

        async with aiohttp.ClientSession(headers=DEFAULT_HEADERS) as self.session:     # TODO move this somewhere
            return await asyncio.gather(*tasks, return_exceptions=True)

    def get_channels(self):
        return Channel.objects.filter(enabled=True)

    async def process_channel(self, channel):
        response, html = await get_with_timeout(self.session, channel.url)
        if not response:
            return 0

        dex = DatasetExtractor(**channel.extractor_settings())
        rowset = dex.extract(html)


        for row in rowset:
            row['url'] = urljoin(channel.url, row['url'])

        url2row = {row['url']: row for row in rowset}
        tracker = URLTracker(channel)
        add, remove = tracker.track(url2row.keys())

        entries = []
        for url in add:
            row = url2row[url]
            self.current_tasks[url] = row
            entry = await self.process_entry(channel, row)
            entries.append(entry)
            self.current_tasks.pop(url)

        print("Channel %s - %d in, %d out" % (channel.title, len(add), len(remove)))
        return len(add)  # Number of processed entries

    async def process_entry(self, channel, entry_dict):
        resp, html = await get_with_timeout(self.session, entry_dict['url'])
        entry = Entry(
            channel=channel,
            url=entry_dict['url'],
            title=entry_dict['title'],
            extra=entry_dict.get('extra')
        )

        if resp:
            items = {}
            entry.final_url=resp.history[-1].url if resp.history else entry_dict['url']
            entry.items=items

        if settings.DEBUG:
            print('Processed %d %s\t\t%s' % (len(self.current_tasks), channel.title, entry_dict['title']))

        return entry



async def get_with_timeout(session, url):
    try:
        with async_timeout.timeout(REQUEST_TIMEOUT, loop=session.loop):
            async with session.get(url) as response:
                response.raise_for_status()
                body = await response.text(errors='ignore')
                # print('GET {} - {} ({} bytes)'.format(url, response.reason, len(body)))
                return response, body
    except asyncio.TimeoutError:
        return None, None
    except aiohttp.HttpProcessingError:
        return None, None
    except UnicodeDecodeError as e:
        print(response)
        raise


class Downloader:
    """Sequential downloader for testing"""

    def __init__(self, cache_dir=None):
        self._jobs = []
        self._cache_dir = self.set_cache_dir(cache_dir)

    def set_cache_dir(self, cache_dir):
        if not cache_dir:
            return None

        if not os.path.isabs(cache_dir):
            cache_dir = os.path.join(os.getcwd(), cache_dir)

        if not os.path.isdir(cache_dir):
            return None

        return cache_dir

    def add_job(self, url, cb):
        self._jobs.append((url, cb))

    def run(self):
        for url, cb in self._jobs:
            text = self.get_cached(url)
            cb(text)

    def get(self, url):
        resp = requests.get(url)

        if resp.ok:
            return resp.text

        return None

    def get_cached(self, url):
        if not self._cache_dir:
            return self.get(url)

        filename = self.cached_filename(url)

        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                return f.read()
        else:
            response = self.get(url)

        if response:
            with open(filename, 'w') as f:
                f.write(response)

        return response

    def cached_filename(self, url):
        md5 = hashlib.md5(url.encode('utf-8'))
        filename = md5.hexdigest()
        return os.path.join(self._cache_dir, filename)


class URLTracker:

    def __init__(self, channel):
        self.channel = channel

    def track(self, new_urls):
        add_urls, remove_urls = list_diff(self.current_urls(), new_urls)
        self.bulk_remove(remove_urls)
        return add_urls, remove_urls

    def bulk_remove(self, urls):
        Entry.objects.filter(channel=self.channel, url__in=urls).delete()

    def current_urls(self):
        rows = Entry.objects.filter(channel=self.channel).values('url')
        return [row['url'] for row in rows]


def list_diff(old, new):
    oldset = set(old)
    newset = set(new)
    return newset - oldset, oldset - newset
