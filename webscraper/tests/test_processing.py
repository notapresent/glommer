import unittest

from webscraper.models import Channel
from webscraper.processing import STATIC_EXTRACTOR_SETTINGS, make_static_extractor, make_channel_extractor

from .util import CHANNEL_DEFAULTS


class ExtractorsTestCase(unittest.TestCase):
    def test_static_extractor_extracts_images(self):
        extractor = make_static_extractor(*STATIC_EXTRACTOR_SETTINGS['images'])
        doc = '''
            <a href="1.JPEG"><img src="1tn.jpg"></a>
            <a href="2.png"><img src="2t.jpg"></a>
            <a href="3.txt"><img src="3t.jpg"></a>  <!-- Wrong filetype, skipped -->
            <a href="4.jpg">Just text</a>        <!-- No thumbnail, skipped -->
            '''
        rv = extractor.extract(doc)
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
        extractor = make_channel_extractor(channel)
        rv = extractor.extract('<a href="1.html" title="extra">Title</a><a>text</a>')
        self.assertEqual(len(rv), 1)
        row = rv[0]
        self.assertEqual(row['extra'], 'extra')
        self.assertEqual(row['title'], 'Title')
        self.assertEqual(row['url'], '1.html')


class ProcessingTestCase(unittest.TestCase):
    def test_process_channel_processes(self):
        pass    # TODO

    def test_process_entry_processes(self):
        pass    # TODO


class ParsingTestCase(unittest.TestCase):
    def test_parse_entry_result(self):
        pass    # TODO

    def test_parse_channel_result(self):
        pass
