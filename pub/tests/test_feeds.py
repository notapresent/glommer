from django.test import TestCase
from pub.feeds import ChannelFeed
from webscraper.tests.util import create_channel, create_entry
from django.test.client import RequestFactory
from django.http.response import Http404


class ChannelFeedTestCase(TestCase):

    def setUp(self):
        super(ChannelFeedTestCase, self).setUp()
        self.rf = RequestFactory()
        self.req = self.rf.get('')
        self.chan = create_channel()
        self.feed = ChannelFeed()
        self.entry = create_entry(channel=self.chan, status=1)

    def test_get_object_returns_object_by_slug(self):
        rv = self.feed.get_object(self.req, self.chan.slug)
        self.assertEquals(self.chan, rv)

    def test_get_object_raises_404(self):
        with self.assertRaises(Http404):
            self.feed.get_object(self.req, 'non-existent-slug')

    def test_title_returls_channel_title(self):
        self.assertEqual(self.feed.title(self.chan), self.chan.title)

    def test_link_returls_channel_url(self):
        self.assertEqual(self.feed.link(self.chan), self.chan.url)

    def test_description_returls_description(self):
        self.assertIn(self.chan.title, self.feed.description(self.chan))

    def test_items_filters_by_channel(self):
        other_channel = create_channel()
        other_entry = create_entry(channel=other_channel)
        rv = self.feed.items(self.chan)
        self.assertEqual(list(rv), [self.entry])

    def test_items_filters_by_status(self):
        entry2 = create_entry(channel=self.chan, status=2)
        entry3 = create_entry(channel=self.chan, status=3)
        rv = self.feed.items(self.chan)
        self.assertEqual(list(rv), [self.entry])

    def test_item_link_returns_url(self):
        entry = create_entry(channel=self.chan)
        self.assertEquals(self.feed.item_link(entry), entry.url)

    def test_item_title_returns_title(self):
        self.assertEquals(self.feed.item_title(self.entry), self.entry.title)

    def test_item_description_uses_template(self):
        response = self.client.get('/public/feeds/%s/rss/' % self.chan.slug)
        self.assertTemplateUsed(response, 'entry_description.html')

    def test_entry_items_are_in_item_description(self):
        response = self.client.get('/public/feeds/%s/rss/' % self.chan.slug)
        content = str(response.content)
        for set_name, set_urls in self.entry.items.items():
            self.assertIn(set_name, content)
            for url in set_urls:
                self.assertIn(url, content)
