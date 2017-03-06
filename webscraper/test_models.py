from django.test import TestCase

from .models import Channel, Entry


channel_defaults = {
    'title': 'Channel title',
    'interval': Channel.INTERVAL_CHOICES[0][0],
    'enabled': True,
    'url': 'http://example.com/',
    'row_selector': 'dummy selector',
    'url_selector': 'dummy selector',
    'title_selector': 'dummy selector',
    'extra_selector': 'dummy selector'
}


def make_channel(**fields):
    defaults = channel_defaults.copy()
    defaults.update(fields)
    return Channel.objects.create(**defaults)


class ChannelTestCase(TestCase):
    def test_model_fields(self):
        channel = make_channel()
        for field in channel_defaults.keys():
            self.assertEqual(getattr(channel, field), channel_defaults[field])

    def test_slug_not_empty(self):
        channel = make_channel()
        self.assertNotEqual(channel.slug, '')
        self.assertIsNotNone(channel.slug)


class EntryTestCase(TestCase):
    def test_model_fields(self):
        chan = make_channel()

        entry_fields = {
            'channel': chan,
            'url': 'http://example.com/',
            'title': 'Test entry title',
            'extra': '',
            'final_url': '',
            'items': None,
        }

        entry = Entry.objects.create(**entry_fields)

        for field in entry_fields.keys():
            self.assertEqual(getattr(entry, field), entry_fields[field])
