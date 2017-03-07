import timeit
import unittest

from webscraper.models import Channel, Entry
from webscraper.services import Downloader, URLTracker

from .util import create_channel, create_entry


class DownloaderTestCase(unittest.TestCase):
    def test_downloads(self):
        def cb(text):
            self.assertIn('origin', text)

        d = Downloader()
        d.add_job('https://httpbin.org/ip', cb)
        d.run()

    def test_cacing(self):
        url = 'https://httpbin.org/get?testheader=1'
        d = Downloader(cache_dir='.localdata/cache')
        d.add_job(url, lambda t: None)
        d.run()
        d.add_job(url, lambda t: self.assertIn('testheader', t))
        elapsed = timeit.timeit(d.run, number=1)
        self.assertLess(elapsed, 0.001)


class URLTrackerTestCase(unittest.TestCase):
    def test_returns_iterable(self):
        ut = URLTracker(None)
        new_entries = ut.filter([])
        try:
            iter(new_entries)
        except TypeError:
            self.fail("filter method must return iterable")

    def test_get_query(self):
        channel = create_channel()
        for i in range(10):
            create_entry(channel=channel, url='http://example.com/%s' % i)

        ut = URLTracker(channel)
        rv = ut.query()
        # self.assertEqual(len(rv), 10)


