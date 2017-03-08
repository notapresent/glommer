import timeit
import unittest

from webscraper.models import Channel, Entry
from webscraper.services import Downloader, URLTracker, rowset_diff, rowset_to_map

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
    def test_filter_returns_iterable(self):
        channel = create_channel()

        ut = URLTracker(channel)
        new_entries = ut.track([])
        try:
            iter(new_entries)
        except TypeError:
            self.fail("filter method must return iterable")

    def test_query(self):
        channel = create_channel()
        entry = create_entry(channel=channel)
        ut = URLTracker(channel)
        rv = ut.query()
        self.assertEqual(len(rv), 1)
        row = rv[0]
        self.assertEqual(row['url'], entry.url)
        self.assertEqual(row['id'], entry.id)

class ServicesTestCase(unittest.TestCase):
    def test_rowset_diff_returns_new_rows(self):
        current_rowset = [
            {'url': 'http://host.com/1'},
            {'url': 'http://host.com/2'},
        ]

        new_rowset = [
            {'url': 'http://host.com/2'},
            {'url': 'http://host.com/3'},
        ]

        add, remove = rowset_diff(current_rowset, new_rowset)

        self.assertEqual(add, [new_rowset[1]])
        self.assertEqual(remove, [current_rowset[0]])


    def test_rowset_to_map(self):
        rowset = [
            {'id': 1, 'url': 'http://host.com/1'},
            {'id': 2, 'url': 'http://host.com/2'}
        ]
        keyname = 'url'
        mapping = rowset_to_map(rowset, keyname)

        self.assertEqual(len(mapping), len(rowset))
        for row in rowset:
            self.assertEqual(mapping[row[keyname]], row)





