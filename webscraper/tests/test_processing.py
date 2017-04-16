import unittest
from unittest import mock

from webscraper.models import Channel, Entry
from webscraper.processing import process_channel, process_entry, parse_channel, parse_entry
from webscraper.futurelite import FutureLite
from webscraper.aiohttpdownloader import DownloadError
from webscraper.extractors import ParseError, EntryExtractor

from django.core.exceptions import ValidationError

from django.test import TestCase
from .util import create_channel, CHANNEL_DEFAULTS, ENTRY_DEFAULTS


class FakeResponse:
    """Aiohttp.response stub"""
    url = 'http://host.com/'


class ProcessChannelTestCase(TestCase):
    GOOD_HTML = '<html><a href="1.html">Title</a></html>'

    def setUp(self):
        self.channel = Channel(**CHANNEL_DEFAULTS)
        self.future = FutureLite()

    def test_sets_status_ok(self):
        self.future.set_result((FakeResponse(), self.GOOD_HTML))
        rv = process_channel(self.channel, self.future)
        self.assertEqual(self.channel.status, Channel.ST_OK)

    def test_sets_status_warn_if_no_entries(self):
        self.future.set_result((FakeResponse(), '<html>No entries here</html>'))
        rv = process_channel(self.channel, self.future)
        self.assertEqual(self.channel.status, Channel.ST_WARNING)

    def test_sets_status_error_on_parse_error(self):
        self.future.set_exception(ParseError('test'))
        process_channel(self.channel, self.future)
        self.assertEqual(self.channel.status, Channel.ST_ERROR)

    def test_sets_status_warning_on_download_error(self):
        self.future.set_exception(DownloadError('test'))
        process_channel(self.channel, self.future)
        self.assertEqual(self.channel.status, Channel.ST_WARNING)

    def test_returns_new_entries(self):
        self.channel.save()
        entry_fields = ENTRY_DEFAULTS.copy()
        entry_fields['url'] = 'http://old_url.com'
        e = Entry(channel=self.channel, **entry_fields).save()
        self.future.set_result((FakeResponse(), self.GOOD_HTML))
        rv = process_channel(self.channel, self.future)
        self.assertEqual(len(rv), 1)


class ParseChannelTestCase(unittest.TestCase):

    def setUp(self):
        self.channel = Channel(**CHANNEL_DEFAULTS)

    def test_skips_invalid_entries(self):
        rv1 = parse_channel(self.channel, '', '<a href="invalid_url">Title</a>')  # invalid URL
        rv2 = parse_channel(self.channel, '', '<a href="http://host.com/"></a>')  # Empty title
        self.assertEqual(len(list(rv1)), 0)
        self.assertEqual(len(list(rv2)), 0)

    def test_makes_absolute_urls(self):
        rv = parse_channel(self.channel, 'http://host.com/', '<a href="1.html">Title</a>')
        entry = next(rv)
        self.assertEqual(entry.url, 'http://host.com/1.html')


class ProcessEntryTestCase(unittest.TestCase):
    GOOD_HTML = '<a href="1.jpg"><img src="1tn.jpg"></a>'

    def setUp(self):
        self.entry = Entry(**ENTRY_DEFAULTS)
        self.future = FutureLite()

    def test_sets_status_ok(self):
        self.future.set_result((FakeResponse(), self.GOOD_HTML))
        rv = process_entry(self.entry, self.future)
        self.assertEqual(self.entry.status, Entry.ST_OK)

    def test_sets_status_error_if_download_error(self):
        self.future.set_exception(DownloadError('test'))
        rv = process_entry(self.entry, self.future)
        self.assertEqual(self.entry.status, Entry.ST_ERROR)

    def test_sets_status_error_if_parse_error(self):
        self.future.set_exception(ParseError('test'))
        rv = process_entry(self.entry, self.future)
        self.assertEqual(self.entry.status, Entry.ST_ERROR)

    def test_sets_status_warning_if_no_items(self):
        self.future.set_result((FakeResponse(), '<html></html>'))
        rv = process_entry(self.entry, self.future)
        self.assertEqual(self.entry.status, Entry.ST_WARNING)


class ParseEntryTestCase(unittest.TestCase):

    GOOD_HTML = '<a href="1.jpg"><img src="1tn.jpg"></a>'

    def test_removes_empty_sets(self):
        rv = parse_entry('http://host.com/', self.GOOD_HTML)
        self.assertEqual(len(rv), 1)

    def test_sets_absolute_urls(self):
        rv = parse_entry('http://host.com/', self.GOOD_HTML)
        extracted_image_url = rv['images'][0]
        self.assertEqual(extracted_image_url, 'http://host.com/1.jpg')
