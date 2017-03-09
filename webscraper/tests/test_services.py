import tempfile
import timeit
import unittest

from webscraper.models import Channel, Entry
from webscraper.services import Downloader, URLTracker, list_diff

from .util import create_channel, create_entry, ENTRY_DEFAULTS


class DownloaderTestCase(unittest.TestCase):

    def test_downloads(self):
        def cb(text):
            self.assertIn('origin', text)

        d = Downloader()
        d.add_job('https://httpbin.org/ip', cb)
        d.run()

    def test_cacing(self):
        url = 'https://httpbin.org/get?testheader=1'
        with tempfile.TemporaryDirectory() as cache_dir:
            d = Downloader(cache_dir=cache_dir)
            d.add_job(url, lambda t: None)
            d.run()
            d.add_job(url, lambda t: self.assertIn('testheader', t))
            elapsed = timeit.timeit(d.run, number=1)
            self.assertLess(elapsed, 0.01)

    def test_caching_disabled_if_dir_not_exists(self):
        d = Downloader('/some-non-existent-dir')
        self.assertIsNone(d._cache_dir)

class URLTrackerTestCase(unittest.TestCase):

    def test_track_returns_new_rows(self):
        channel = create_channel()
        entry_fields = ENTRY_DEFAULTS.copy()
        entry_fields['channel'] = channel
        test_entries = []
        for i in (1, 2):
            fields = entry_fields.copy()
            fields['url'] = 'http://host.com/%s' % i
            test_entries.append(Entry(**fields))

        Entry.objects.bulk_create(test_entries)
        tracker = URLTracker(channel)

        new_urls = ['http://host.com/2', 'http://host.com/3']
        add, remove = tracker.track(new_urls)
        self.assertEqual(list(add), [new_urls[1]])

    def test_track_deletes_old(self):
        channel = create_channel()
        create_entry(channel=channel)
        tracker = URLTracker(channel)
        tracker.track([])
        self.assertEqual(len(Entry.objects.filter(channel=channel)), 0)

    def test_current_urls(self):
        channel = create_channel()
        entry = create_entry(channel=channel)
        tracker = URLTracker(channel)
        rv = tracker.current_urls()
        self.assertEqual(len(rv), 1)
        self.assertEqual(rv[0], entry.url)


class ServicesTestCase(unittest.TestCase):

    def test_list_diff(self):
        old = [1, 2]
        new = [2, 3]
        add, remove = list_diff(old, new)
        self.assertEqual(list(add), [3])
        self.assertEqual(list(remove), [1])
