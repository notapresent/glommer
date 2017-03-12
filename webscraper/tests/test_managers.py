from django.test import TestCase

from webscraper.models import Channel, Entry
from .util import create_channel, create_entry


class ChannelManagerTestCase(TestCase):

    def test_enabled_returns_enabled(self):
        c1 = create_channel(enabled=True)
        c2 = create_channel(enabled=False)
        channels = list(Channel.objects.enabled())
        self.assertIn(c1, channels)
        self.assertNotIn(c2, channels)


class EntryManagerTestCase(TestCase):

    def setUp(self):
        self.channel = create_channel()
        self.entry = create_entry(channel=self.channel)

    def test_get_id_url_for_channel_returns_fields(self):
        resultset = Entry.objects.get_id_url_for_channel(self.channel)

        self.assertEqual(len(resultset), 1)
        entry_dict = resultset[0]
        self.assertEqual(entry_dict, {'id': self.entry.id, 'url': self.entry.url})

    def test_get_id_url_for_channel_filters_by_channel(self):
        c2 = create_channel()

        resultset1 = Entry.objects.get_id_url_for_channel(self.channel)
        self.assertEqual(len(resultset1), 1)

        resultset2 = Entry.objects.get_id_url_for_channel(c2)
        self.assertEqual(len(resultset2), 0)

    def test_bulk_delete_filters_by_id(self):
        e2 = create_entry(channel=self.channel)
        Entry.objects.delete_from_channel_by_ids(self.channel, [self.entry.id])
        entries = self.channel.entry_set.all()
        self.assertEqual(len(entries), 1)
        self.assertIn(e2, entries)

    def test_bulk_delete_filters_by_channel(self):
        c2 = create_channel()
        e2 = create_entry(channel=c2)
        Entry.objects.delete_from_channel_by_ids(self.channel, [self.entry.id])
        entries = self.channel.entry_set.all()
        c2_entries = c2.entry_set.all()

        self.assertEqual(len(entries), 0)
        self.assertEqual(len(c2_entries), 1)
