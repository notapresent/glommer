from django.test import TestCase
from django.db import connection
from django.conf import settings

from webscraper.models import Entry
from webscraper.insbuffer import InsertBuffer
from .util import create_channel, ENTRY_DEFAULTS


class InsertBufferTestCase(TestCase):
    def setUp(self):
        self._old_debug, settings.DEBUG = settings.DEBUG, True
        self.channel = create_channel()

    def tearDown(self):
        settings.DEBUG = self._old_debug

    def test_batch_insert(self):
        old_num_queries = len(connection.queries)

        with InsertBuffer(5) as buf:
            for _ in range(8):
                buf.add(Entry(channel=self.channel, **ENTRY_DEFAULTS))

        num_queries = len(connection.queries) - old_num_queries

        self.assertEqual(len(self.channel.entry_set.all()), 8)
        self.assertEqual(num_queries, 2)


