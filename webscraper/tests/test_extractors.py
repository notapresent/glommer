import unittest
from unittest.mock import Mock


import lxml.html

from webscraper.extractors import (FieldExtractor, RowExtractor, DatasetExtractor, ensure_element, first_or_none,
                                   EntryExtractor, xpath_tolower, ext_selector_fragment, ParseError, RegexExtractor,
                                   ChannelExtractor, EntryExtractor, link_extractor)
from webscraper.models import Channel
from .util import CHANNEL_DEFAULTS


class RowExtractorTestCase(unittest.TestCase):

    def test_extract_extracts_items(self):
        e = RowExtractor(selector="//p[@class='a']/text()")
        doc = '<div><p class="a">One</p><p class="a">Two</p><p class="b">Three</p></div>'
        rv = e.extract(doc)
        self.assertEqual(len(rv), 2)
        self.assertIn('One', rv)
        self.assertIn('Two', rv)

    def test_extractor_raises_on_invalid_doc(self):
        e = RowExtractor(selector="//p")
        with self.assertRaises(ParseError):
            e.extract('')

    def test_regexp_selector(self):
        self.extractor = RowExtractor(selector="//a[re:test(@href, '\.(jpg|png)$')]/@href")
        self.assertEqual(self.extractor.extract('<a href="1.jpg">1</a>'), ['1.jpg'])
        self.assertEqual(self.extractor.extract('<a href="/dir/2.png.txt">2</a>'), [])


class FieldExtractorTestCase(unittest.TestCase):

    def setUp(self):
        self.extractor = FieldExtractor(selector='//a/text()')

    def test_extract_extracts(self):
        rv = self.extractor.extract('<a>some text</a>')
        self.assertEqual(rv, 'some text')

    def test_extract_returns_1st_element_only(self):
        rv = self.extractor.extract('<p><a>One</a><a>Two</a>')
        self.assertEqual(rv, 'One')


class DatasetExtractorTestCase(unittest.TestCase):

    def test_extract_extracts_rows(self):
        doc = '''<div>
            <a href="1.html">1</a>
            <a href="2.html">2</a>
        </div>'''
        row_selector = '//div/a'
        field_selectors = {
            'text':  'text()',
            'url': '@href'
        }

        e = DatasetExtractor(selector=row_selector, fields=field_selectors)
        rv = e.extract(doc)

        self.assertEqual(len(rv), 2)
        self.assertEqual(rv[0], {'text': '1', 'url': '1.html'})
        self.assertEqual(rv[1], {'text': '2', 'url': '2.html'})


class ChannelExtractorTestCase(unittest.TestCase):
    def test_extacts(self):
        doc = '''<p>
            <a href="1.html">test</a>
        </p>
        '''
        e = ChannelExtractor(row_selector='//p/a', url_selector='@href', title_selector='text()')
        rv = e.extract(doc)
        row = rv[0]
        self.assertEqual(len(rv), 1)
        self.assertEqual(row['url'], '1.html')
        self.assertEqual(row['title'], 'test')


class RegexExtractorTestCase(unittest.TestCase):

    def test_extracts(self):
        ex = RegexExtractor(['doc'])
        doc = '''<html><script>var url='path/to/file.doc';</script></html>'''
        self.assertEquals(ex.extract(doc), ['path/to/file.doc'])


class EntryExtractorTestCase(unittest.TestCase):
    def test_extracts_images(self):
        doc = '<a href="image.jpg"><img src="image_tn.jpg"></a>'
        ee = EntryExtractor()
        rv = ee.extract(doc)
        self.assertEqual(len(rv['images']), 1)

    def test_extracts_movies(self):
        doc = '<a href="movie.avi"><img src="movie_tn.jpg"></a>'
        ee = EntryExtractor()
        rv = ee.extract(doc)
        self.assertEqual(len(rv['videos']), 1)

    def test_extracts_streaming(self):
        doc = '<video><source src="streaming.mp4" type="video/mp4"></video>'
        ee = EntryExtractor()
        rv = ee.extract(doc)
        self.assertEqual(len(rv['streaming']), 1)

    @unittest.mock.patch('webscraper.extractors.link_extractor', autospec=True)
    def test_entry_extractor_uses_same_tree(self, static_extractor):
        me = Mock(DatasetExtractor)
        me.extract.return_value = [{'url': '1'}, {'url': '2'}]
        static_extractor.return_value = me
        ee = EntryExtractor()
        ee.extract('<xml></xml>')
        self.assertEqual(me.extract.call_args_list[0], me.extract.call_args_list[1])

    def test_extract_items_works(self):
        doc = '<a href="movie.avi"><img src="movie_tn.jpg"></a>'
        ee = EntryExtractor()
        self.assertEqual(ee.extract(doc), EntryExtractor.extract_items(doc))

    def test_extract_raises_on_invalid_doc(self):
        ee = EntryExtractor()
        with self.assertRaises(ParseError):
            ee.extract('')

class UtilTestCase(unittest.TestCase):

    def test_ensure_element_returs_htmlelement_from_string(self):
        rv = ensure_element('<p>test</p>')
        self.assertIsInstance(rv, lxml.html.HtmlElement)

    def test_ensure_element_returs_htmlelement_unchanged(self):
        rv = ensure_element('<p>test</p>')
        self.assertIs(rv, ensure_element(rv))

    def test_ensure_element_raises_on_invalid_doc(self):
        with self.assertRaises(ParseError):
            ensure_element(None)

    def test_first_or_none_returns_1st_elem_only(self):
        self.assertEqual(first_or_none(['a', 'b']), 'a')

    def test_first_or_none_returns_scalar_as_is(self):
        o = object()
        self.assertIs(o, first_or_none(o))

    def test_first_or_none_returns_none_on_empty_seq(self):
        self.assertEquals(first_or_none([]), None)

    def test_first_or_none_returns_string_as_is(self):
        s = 'Test'
        self.assertIs(first_or_none(s), s)

    def test_xpath_tolower(self):
        elem = ensure_element('<a href="Test.HTML"></a>')
        rv = elem.xpath(xpath_tolower('@href'))
        self.assertEqual(rv, 'test.html')

    def test_ext_selector_fragment(self):
        selector = ext_selector_fragment('@href', ['jpeg', 'png'])
        rv = FieldExtractor(selector=selector).extract('<a href="file.jpeg"></a>')
        self.assertTrue(rv)

    def test_link_extractor_extracts(self):
        extractor = link_extractor(['png'])
        rv = extractor.extract('<a href="2.png"><img src="2tn.jpg"></a>')
        row = rv[0]
        self.assertEqual(len(rv), 1)
        self.assertEqual(row['url'], '2.png')

    def test_link_extractor_nocase(self):
        extractor = link_extractor(['png'])
        rv = extractor.extract('<a href="2.PNG"><img src="2tn.jpg"></a>')
        self.assertEqual(rv[0]['url'], '2.PNG')
