from django.test import TestCase
from django.db import connection
from django.conf import settings

from webscraper.models import Entry
from webscraper.insbuffer import InsertBuffer, split_chunk
from .util import create_channel, ENTRY_DEFAULTS


class InsertBufferTestCase(TestCase):

    def setUp(self):
        # Turn on debug to record SQL queries
        self._old_debug, settings.DEBUG = settings.DEBUG, True
        self.channel = create_channel()
        self.buf = InsertBuffer(3)

    def tearDown(self):
        settings.DEBUG = self._old_debug

    def test_batch_insert(self):
        old_num_queries = len(connection.queries)

        with self.buf as buffer:
            for i in range(5):
                entry = Entry(channel=self.channel, **ENTRY_DEFAULTS)
                entry.url = 'http://ho.st/%d' % i
                buffer.add(entry)

        num_queries = len(connection.queries) - old_num_queries

        self.assertEqual(len(self.channel.entry_set.all()), 5)
        self.assertEqual(num_queries, 2)
        self.assertEqual(len(self.buf), 0)

    def test_len(self):
        for _ in range(2):
            self.buf.add(Entry(channel=self.channel, **ENTRY_DEFAULTS))
        self.assertEquals(len(self.buf), 2)

    def test_split_chunk_splits(self):
        val = [1, 2, 3]
        chunk, remainder = split_chunk(val, 2)
        self.assertEquals(chunk, [1, 2])
        self.assertEquals(remainder, [3])
