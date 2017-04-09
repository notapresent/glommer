from unittest.mock import patch

from django.test import TestCase
from django.utils.six import StringIO
from .util import create_channel

from webscraper.management.commands.scrape import Command


class ScrapeCommandTestCase(TestCase):

    def setUp(self):
        self.stdout = StringIO()
        self.cmd = Command(stdout=self.stdout, no_color=True)

    @patch('webscraper.management.commands.scrape.scrape')
    def test_handle_calls_scrape(self, mocked_scrape):
        channel = create_channel()
        self.cmd.handle()
        self.assertEquals(mocked_scrape.call_count, 1)
        call_args, _ = mocked_scrape.call_args
        self.assertEquals(list(call_args[0]), [channel])
