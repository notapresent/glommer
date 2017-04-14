from django.test import TestCase

from webscraper.models import Channel, Entry

from .util import CHANNEL_DEFAULTS, ENTRY_DEFAULTS, create_channel, create_entry


class ChannelTestCase(TestCase):

    def test_model_fields(self):
        channel = create_channel()
        for fieldname, fieldvalue in CHANNEL_DEFAULTS.items():
            self.assertEqual(getattr(channel, fieldname), fieldvalue)

    def test_slug_not_empty(self):
        channel = create_channel()
        self.assertNotEqual(channel.slug, '')
        self.assertIsNotNone(channel.slug)

    def test_unique_slug_creation(self):
        channel = create_channel()
        other_channel = Channel(**CHANNEL_DEFAULTS)
        other_channel.slug = channel.slug
        other_channel.save()
        self.assertNotEqual(channel.slug, other_channel.slug)


class EntryTestCase(TestCase):

    def test_model_fields(self):
        entry = create_entry()

        for fieldname, fieldvalue in ENTRY_DEFAULTS.items():
            self.assertEqual(getattr(entry, fieldname), fieldvalue)

    def test_real_url(self):
        e1 = create_entry(url='http://one.com')
        e2 = create_entry(url='http://one.com', final_url='http://two.com')
        self.assertEqual(e1.real_url, 'http://one.com')
        self.assertEqual(e2.real_url, 'http://two.com')

    def test_channel_url_constraint(self):
        c = create_channel()
        e1 = create_entry(channel=c, url='http://host.com/1')
        e2 = Entry(channel=c, **ENTRY_DEFAULTS)
        e2.url = 'http://host.com/1'

        with self.assertRaises(Exception):
            e2.save()



