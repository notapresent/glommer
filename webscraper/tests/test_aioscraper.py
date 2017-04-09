import asyncio

from django.test import TestCase

from webscraper.models import Channel, Entry
from webscraper.aioscraper import AioScraper
from .util import create_channel, create_entry, ENTRY_DEFAULTS


class AioHttpScraperTestCase(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)


class ScrapeFuncionsTestCase(TestCase):
    pass
