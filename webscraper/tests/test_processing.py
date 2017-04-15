import unittest
from unittest import mock

from webscraper.models import Channel, Entry
from webscraper.processing import (process_channel, process_entry, parse_channel, populate_entry, normalize_item_set,
                                   normalize_channel_row, postprocess_items, highest_resolution)
from webscraper.futurelite import FutureLite
from webscraper.aiohttpdownloader import DownloadError
from webscraper.extractors import ParseError, EntryExtractor

from django.core.exceptions import ValidationError

from django.test import TestCase
from .util import create_channel, CHANNEL_DEFAULTS, ENTRY_DEFAULTS


class FakeResponse:
    """Aiohttp.response stub"""
    url = 'http://host.com/'


class FakeEntryExtractor:
    """EntryExtractor stub"""

    DEFAULT_EXTRACT_RV = {
        'images': [],
        'videos': ['1.avi', 'http://ho.st/2.avi']
    }

    def __init__(self, extract_rv=None):
        self._extract_rv = extract_rv if extract_rv is not None else self.DEFAULT_EXTRACT_RV

    def extract(self, _):
        return self._extract_rv

    def extract_field(self, field_selector, html):
        return self._extract_rv


class ChannelProcessingTestCase(TestCase):

    def setUp(self):
        self.channel = Channel(**CHANNEL_DEFAULTS)
        self.response = FakeResponse()
        self.future = FutureLite()
        self.future.set_result((self.response, '<html></html>'))

    def test_sets_status_ok(self):
        process_channel(self.channel, self.future)
        self.assertEqual(self.channel.status, Channel.ST_OK)

    def test_sets_status_error_on_parse_error(self):
        badfuture = FutureLite()
        badfuture.set_exception(ParseError('test'))
        process_channel(self.channel, badfuture)
        self.assertEqual(self.channel.status, Channel.ST_ERROR)

    def test_sets_status_warning_on_download_error(self):
        badfuture = FutureLite()
        badfuture.set_exception(DownloadError('test'))
        process_channel(self.channel, badfuture)
        self.assertEqual(self.channel.status, Channel.ST_WARNING)

    def test_saves(self):
        process_channel(self.channel, self.future)
        self.assertIsNotNone(self.channel.id)

    def test_returns_entries(self):
        fields = ENTRY_DEFAULTS.copy()
        fields.pop('url')
        entries = [Entry(channel=self.channel, url=str(i), **fields) for i in range(3)]
        with mock.patch('webscraper.processing.parse_channel') as mock_parse_channel:
            mock_parse_channel.return_value = entries
            rv = process_channel(self.channel, self.future)

        self.assertEqual(len(rv), len(entries))

    def test_parse_channel_skips_invalid_entries(self):
        channel = Channel(**CHANNEL_DEFAULTS)
        doc = '<html><a href="invaid url" title="test title">Test</a></html>'
        rv = parse_channel(channel, 'http://host.com/', doc)
        self.assertEquals(len(list(rv)), 0)


class EntryProcessingTestCase(unittest.TestCase):

    def setUp(self):
        self.channel = Channel(**CHANNEL_DEFAULTS)
        self.entry = Entry(channel=self.channel, **ENTRY_DEFAULTS)
        self.future = FutureLite()
        self.future.set_result((FakeResponse(), ''))
        self.extractor = FakeEntryExtractor()

    def test_sets_status_ok(self):
        process_entry(self.entry, self.future, self.extractor)
        self.assertEqual(self.entry.status, Entry.ST_OK)

    def test_sets_status_warn(self):
        self.extractor = FakeEntryExtractor({})
        process_entry(self.entry, self.future, self.extractor)
        self.assertEqual(self.entry.status, Entry.ST_WARNING)

    def test_sets_status_error_on_download_error(self):
        future = FutureLite()
        future.set_exception(DownloadError('test'))
        process_entry(self.entry, future, self.extractor)
        self.assertEqual(self.entry.status, Entry.ST_ERROR)

    def test_sets_status_error_on_parse_error(self):
        future = FutureLite()
        future.set_exception(ParseError('test'))
        process_entry(self.entry, future, self.extractor)
        self.assertEqual(self.entry.status, Entry.ST_ERROR)

    def test_sets_final_url(self):
        resp, _ = self.future.result()
        self.entry.url = resp.url
        process_entry(self.entry, self.future, self.extractor)
        self.assertEqual(self.entry.final_url, '')

        entry = Entry(channel=self.channel, **ENTRY_DEFAULTS)
        entry.url = 'http://some-other-url,com/'
        process_entry(entry, self.future, self.extractor)
        self.assertEqual(entry.final_url, resp.url)

    def test_postprocess_items_deduplicates(self):
        items = {
            'key1': ['1', '2'],
            'key2': ['2', '3'],
        }
        rv = postprocess_items(items, '')
        resulting_items = [url for sublist in rv.values() for url in sublist]
        self.assertEqual(len(resulting_items), len(set(resulting_items)))


class ParsingTestCase(unittest.TestCase):

    # def test_populate_entry_populates(self):
    #     ee = EntryExtractor()
    #     entry = Entry(title='title', url='http://ho.st/', channel_id=1)
    #     populate_entry(entry, '<a href="1.html"><img src="1th.jpg"></a>', ee)

    #     self.assertEqual(entry.items, 1)
    #     iset_name, iset = entry.items.popitem()

    #     self.assertEqual(iset_name, 'images')
    #     for url in iset:
    #         self.assertTrue(url.startswith(entry.real_url))

    # @mock.patch('webscraper.processing.DatasetExtractor')
    # def test_parse_channel_result(self, dse):   # TODO split this
    #     base_url = 'http://ho.st/'
    #     mock_extractor = unittest.mock.Mock()
    #     mock_extractor.extract.return_value = [
    #         {'url': '1.html', 'title': 'title 1', 'extra': 'extra 1'},
    #         {'url': base_url + '2.html', 'title': 'title 2', 'extra': 'extra 2'}
    #     ]
    #     dse.return_value = mock_extractor
    #     channel = Channel(**CHANNEL_DEFAULTS)
    #     rv = list(parse_channel(channel, base_url, ''))
    #     self.assertEqual(len(rv), 2)
    #     self.assertIsInstance(rv[0], Entry)
    #     self.assertIsInstance(rv[1], Entry)
    #     self.assertIs(rv[0].channel, channel)

    def test_normalize_channel_row(self):
        row = {'url': ' http://host.com/ ', 'title': ' title ', 'extra': ' extra'}
        rv = normalize_channel_row(row)
        self.assertEqual(rv, {'url': 'http://host.com/', 'title': 'title', 'extra': 'extra'})

    def test_normalize_item_set(self):
        rv = normalize_item_set(['1', ' 2', ' 1 '])
        self.assertEqual(len(rv), 2)
        self.assertIn('1', rv)
        self.assertIn('2', rv)


class HighestResolutionTestCase(unittest.TestCase):

    def test_groups_by_same_url(self):
        urls = [
            'http://host.com/path/79296_sd_480p.mp4',
            'http://host.com/path/79296_sd_360p.mp4'
        ]
        rv = highest_resolution(urls)
        self.assertEquals(rv, [urls[0]])

    def test_leaves_varying_urls_as_is(self):
        urls = [
            'http://host.com/path/file1_sd_480p.mp4',
            'http://host.com/path/file2_sd_360p.mp4'
        ]
        rv = highest_resolution(urls)
        self.assertEquals(len(rv), 2)
