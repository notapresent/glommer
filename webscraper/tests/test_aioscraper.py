import asyncio

from django.test import TestCase

from webscraper.models import Channel, Entry
from webscraper.aioscraper import AioScraper
from .util import create_channel, create_entry, ENTRY_DEFAULTS


class AioHttpScraperTestCase(TestCase):
    pass
