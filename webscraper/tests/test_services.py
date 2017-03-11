from django.test import TestCase

from webscraper.models import Channel, Entry
from webscraper.services import Scraper, URLTracker, list_diff
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
