import asyncio
import aiohttp

from django.test import TestCase

from webscraper.models import Channel, Entry
from webscraper.services import AioHttpScraper, URLTracker, list_diff, get
from .util import create_channel, create_entry, ENTRY_DEFAULTS


class URLTrackerTestCase(TestCase):

    def setUp(self):
        self.channel = create_channel()
        self.entry = create_entry(channel=self.channel)

    def test_track_returns_new_rows(self):
        e1 = create_entry(channel=self.channel, url='http://host.com/1')
        e2 = create_entry(channel=self.channel, url='http://host.com/2')
        new_urls = ['http://host.com/2', 'http://host.com/3']

        tracker = URLTracker(self.channel)
        add, remove = tracker.track(new_urls)
        self.assertEqual(list(add), [new_urls[1]])

    def test_track_deletes_old(self):
        tracker = URLTracker(self.channel)
        tracker.track([])
        entryset = self.channel.entry_set.all()
        self.assertEqual(len(entryset), 0)

    def test_get_current_urls_to_ids(self):
        tracker = URLTracker(self.channel)
        rv = tracker.get_current_urls_to_ids()
        self.assertEqual(len(rv), 1)
        self.assertIn(self.entry.url, rv)
        self.assertEqual(rv[self.entry.url], self.entry.id)


class ServicesTestCase(TestCase):

    def test_list_diff(self):
        old = [1, 2]
        new = [2, 3]
        add, remove = list_diff(old, new)
        self.assertEqual(list(add), [3])
        self.assertEqual(list(remove), [1])


class AioHttpScraperTestCase(TestCase):

    def test_run_returns_2_num_tuple(self):
        scr = AioHttpScraper()
        v1, v2 = scr.run()
        self.assertIsInstance(v1, int)
        self.assertIsInstance(v2, int)

    def test_run_returns_number_of_active_channels(self):
        create_channel()
        scr = AioHttpScraper()
        v1, v2 = scr.run()
        enabled_channels = Channel.objects.enabled()
        self.assertEqual(v1, len(enabled_channels))

    def test_run_returns_number_of_processed_entries(self):
        channel = create_channel()
        entries = [Entry(channel=channel) for _ in range(2)]
        Entry.objects.bulk_create(entries)

        scr = AioHttpScraper()
        v1, v2 = scr.run()
        self.assertEqual(v2, len(entries))


class AioHttpDownloaderTestCase(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    def test_get_downloads(self):
        async def go():
            async with aiohttp.ClientSession(loop=self.loop) as sess:
                return await get('http://httpbin.org/get?testString', sess)

        resp, body = self.loop.run_until_complete(go())
        self.assertIn('testString', body)
