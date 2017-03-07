import collections
import unittest

import lxml.html

from webscraper.extractors import FieldExtractor, RowExtractor, DatasetExtractor, ensure_element, scalar


class FieldExtractorTestCase(unittest.TestCase):
    def setUp(self):
        self.extractor = FieldExtractor(selector='//a/text()')

    def test_extract_extracts(self):
        rv = self.extractor.extract('<a>some text</a>')
        self.assertEqual(rv, 'some text')

    def test_extract_accepts_lxml_htmlelement(self):
        elem = lxml.html.fragment_fromstring('<a>test text</a>')
        rv = self.extractor.extract(elem)
        self.assertEqual(rv, 'test text')

    def test_extract_returns_1st_element_only(self):
        rv = self.extractor.extract('<p><a>One</a><a>Two</a>')
        self.assertEqual(rv, 'One')


class RowExtractorTestCase(unittest.TestCase):
    def test_extract_extracts_items(self):
        e = RowExtractor(selector="//p[@class='a']")
        doc = '<div><p class="a">One</p><p class="a">Two</p><p class="b">Three</p></div>'
        rv = e.extract(doc)
        self.assertEqual(len(rv), 2)
        self.assertEqual(rv[0].text, 'One')
        self.assertEqual(rv[1].text, 'Two')


class DatasetExtractorTestCase(unittest.TestCase):
    def setUp(self):
        self.doc = '''
        <div>
            <p><a>1-1</a><i>1-2</i></p>
            <p><a>2-1</a><i>2-2</i></p>
        </div>
        '''
        self.row_selector = '//div/p'
        self.field_selectors = {
            'col1': {'selector': './a/text()'},
            'col2': {'selector': './i/text()'}
        }

    def test_extract_extracts(self):
        e = DatasetExtractor(selector=self.row_selector, fields=self.field_selectors)
        rv = e.extract(self.doc)
        self.assertEqual(len(rv), 2)
        self.assertEqual(rv[0], {'col1': '1-1', 'col2': '1-2'})
        self.assertEqual(rv[1], {'col1': '2-1', 'col2': '2-2'})


class UtilsTestCase(unittest.TestCase):
    def test_ensure_element_returs_htmlelement(self):
        doc = '<p>test</p>'
        elem = lxml.html.fromstring(doc)
        self.assertIsInstance(ensure_element(doc), lxml.html.HtmlElement)
        self.assertIsInstance(ensure_element(elem), lxml.html.HtmlElement)

    def test_scalar_returns_1st_elem_only(self):
        rv = self.assertEqual(scalar(['a', 'b']), 'a')
