import unittest
from unittest import mock

from webscraper.models import Channel, Entry
from webscraper.processing import (STATIC_EXTRACTOR_SETTINGS, make_static_extractor, make_channel_extractor,
                                   process_channel, process_entry, parse_channel, parse_entry, normalize_item_set,
                                   normalize_channel_row, make_entry_extractor, make_entry, ensure_entry_title,
                                   highest_resolution, postprocess_items)
from webscraper.futurelite import FutureLite
from webscraper.aiohttpdownloader import DownloadError
from webscraper.extractors import ParseError
from django.db.models import Model
from django.core.exceptions import ValidationError

from django.test import TestCase
from .util import create_channel, CHANNEL_DEFAULTS, ENTRY_DEFAULTS


class ExtractorsTestCase(unittest.TestCase):
    IMAGES_TEST_DOC = '''
            <a href="1.JPEG"><img src="1tn.jpg"></a>
            <a href="2.png"><img src="2t.jpg"></a>
            <a href="3.txt"><img src="3t.jpg"></a>  <!-- Wrong filetype, skipped -->
            <a href="4.jpg">Just text</a>        <!-- No thumbnail, skipped -->
        '''

    def test_static_extractor_extracts_images(self):
        extractor = make_static_extractor(*STATIC_EXTRACTOR_SETTINGS['images'])

        rv = extractor.extract(self.IMAGES_TEST_DOC)
        self.assertEqual(len(rv), 2)
        self.assertIn({'url': '1.JPEG'}, rv)
        self.assertIn({'url': '2.png'}, rv)

    def test_video_extractor_extracts_videos(self):
        extractor = make_static_extractor(*STATIC_EXTRACTOR_SETTINGS['videos'])
        doc = '''
            <a href="1.avi"><img src="1tn.jpg"></a>
            <a href="2.Mpg"><img src="2t.jpg"></a>
        '''
        rv = extractor.extract(doc)
        self.assertEqual(len(rv), 2)
        self.assertIn({'url': '1.avi'}, rv)
        self.assertIn({'url': '2.Mpg'}, rv)

    def test_make_channel_extractor(self):
        channel = Channel(**CHANNEL_DEFAULTS)
        channel.extra_selector = '@title'
        extractor = make_channel_extractor(channel)
        rv = extractor.extract('<a href="1.html" title="extra">Title</a><a>text</a>')
        self.assertEqual(len(rv), 1)
        row = rv[0]
        self.assertEqual(row['extra'], 'extra')
        self.assertEqual(row['title'], 'Title')
        self.assertEqual(row['url'], '1.html')

    def test_make_entry_extractor_returns_extractor(self):
        ee = make_entry_extractor()
        rv = ee.extract(self.IMAGES_TEST_DOC)
        self.assertEqual(len(rv['images']), 2)
        self.assertEqual(len(rv['videos']), 0)
        self.assertEqual(len(rv['streaming']), 0)

    def test_extractor_extracts_nested(self):
        doc = '''
        <a href="1.jpg"><font style="">
        <img src="1tn.jpg">
        Some text
        </font></a>
        '''
        ee = make_entry_extractor()
        rv = ee.extract(doc)
        self.assertEqual(rv['images'], [{'url': '1.jpg'}])


class FakeResponse:
    """Aiohttp.response stub"""
    url = 'http://host.com/'


class FakeEntryExtractor:
    """EntryExtractor stub"""

    DEFAULT_EXTRACT_RV = {
        'images': [],
        'videos': [{'url': '1.avi'}, {'url': 'http://ho.st/2.avi'}]
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

    def test_make_entry_returns_entry(self):
        row = {'url': 'http://host.com', 'title': 'test'}
        rv = make_entry(row)
        self.assertEquals(rv.url, 'http://host.com')
        self.assertEquals(rv.title, 'test')
        self.assertIs(rv.__class__, Entry)
        self.assertIsInstance(rv, Model)

    def test_make_entry_raises_on_invalid_row(self):
        row = {'url': 'invalid url', 'title': ''}
        with self.assertRaises(ValidationError):
            make_entry(row)


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

    def test_ensure_entry_title_returns_title_if_set(self):
        e = Entry(**ENTRY_DEFAULTS)
        original_title = e.title
        ensure_entry_title(e, '<html></html', FakeEntryExtractor())
        self.assertEquals(e.title, original_title)

    def test_ensure_entry_title_extracts_title_if_not_set(self):
        e = Entry(**ENTRY_DEFAULTS)
        e.title = ''
        ensure_entry_title(e, '<html></html', FakeEntryExtractor('new title'))
        self.assertEquals(e.title, 'new title')

    def test_ensure_entry_title_raises(self):
        e = Entry(**ENTRY_DEFAULTS)
        e.title = ''
        with self.assertRaises(ParseError):
            ensure_entry_title(e, '<html></html', FakeEntryExtractor(''))

    def test_postprocess_items_deduplicates(self):
        items = {
            'key1': ['1', '2'],
            'key2': ['2', '3'],
        }
        rv = postprocess_items(items)
        resulting_items = [url for sublist in rv.values() for url in sublist]
        self.assertEqual(len(resulting_items), len(set(resulting_items)))


class ParsingTestCase(unittest.TestCase):

    def test_parse_entry_result(self):
        ee = FakeEntryExtractor()
        entry = Entry(title='title', url='http://ho.st/', channel_id=1)
        rv = parse_entry(entry, '', ee)

        self.assertEqual(len(rv), 1)
        iset_name, iset = rv.popitem()

        self.assertEqual(iset_name, 'videos')
        for url in iset:
            self.assertTrue(url.startswith(entry.real_url))

    @mock.patch('webscraper.processing.DatasetExtractor')
    def test_parse_channel_result(self, dse):   # TODO split this
        base_url = 'http://ho.st/'
        mock_extractor = unittest.mock.Mock()
        mock_extractor.extract.return_value = [
            {'url': '1.html', 'title': 'title 1', 'extra': 'extra 1'},
            {'url': base_url + '2.html', 'title': 'title 2', 'extra': 'extra 2'}
        ]
        dse.return_value = mock_extractor
        channel = Channel(**CHANNEL_DEFAULTS)
        rv = list(parse_channel(channel, base_url, ''))
        self.assertEqual(len(rv), 2)
        self.assertIsInstance(rv[0], Entry)
        self.assertIsInstance(rv[1], Entry)
        self.assertIs(rv[0].channel, channel)

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
