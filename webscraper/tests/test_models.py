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

    def test_extractor_settings(self):
        channel = create_channel()
        rv = channel.extractor_settings()
        self.assertEqual(rv['selector'], CHANNEL_DEFAULTS['row_selector'])
        self.assertEqual(len(rv['fields']), 3)
        self.assertEqual(rv['fields']['url'], {'selector': CHANNEL_DEFAULTS['url_selector']})
        self.assertEqual(rv['fields']['title'], {'selector': CHANNEL_DEFAULTS['title_selector']})
        self.assertEqual(rv['fields']['extra'], {'selector': CHANNEL_DEFAULTS['extra_selector']})


class EntryTestCase(TestCase):

    def test_model_fields(self):
        entry = create_entry()

        for fieldname, fieldvalue in ENTRY_DEFAULTS.items():
            self.assertEqual(getattr(entry, fieldname), fieldvalue)
