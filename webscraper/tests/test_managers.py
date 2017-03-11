from django.test import TestCase

from webscraper.models import Channel, Entry
from .util import create_channel

class ChannelManagerTestCase(TestCase):
    def test_enabled_returns_enabled(self):
        c1 = create_channel(enabled=True)
        c2 = create_channel(enabled=False)
        channels = list(Channel.objects.enabled())
        self.assertIn(c1, channels)
        self.assertNotIn(c2, channels)
