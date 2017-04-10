import asyncio
import unittest
from webscraper.models import Channel, Entry


CHANNEL_DEFAULTS = {
    'title': 'Channel title',
    'interval': Channel.INTERVAL_CHOICES[0][0],
    'enabled': True,
    'url': 'http://example.com/',
    'row_selector': '//a[@href]',
    'url_selector': '@href',
    'title_selector': 'text()',
    'extra_selector': '@title'
}

ENTRY_DEFAULTS = {
    'url': 'http://example.com/',
    'title': 'Test entry title',
    'extra': '',
    'final_url': '',
    'items': {'images': ['1.jpg', '2.jpg'], 'videos': ['1.avi', '2.avi']}
}


def create_channel(**override_fields):
    fields = CHANNEL_DEFAULTS.copy()
    fields.update(override_fields)
    return Channel.objects.create(**fields)


def create_entry(**override_fields):
    fields = ENTRY_DEFAULTS.copy()
    fields.update(override_fields)
    fields.setdefault('channel', create_channel())
    return Entry.objects.create(**fields)



class AsyncioTestCase(unittest.TestCase):
    def setUp(self):
        super(AsyncioTestCase, self).setUp()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()
        super(AsyncioTestCase, self).tearDown()
