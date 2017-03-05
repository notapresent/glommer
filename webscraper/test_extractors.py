import collections
import unittest

import lxml.html

from .extractors import FieldExtractor, RowExtractor, ensure_element, scalar


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
    def test_extract_returns_seq(self):
        e = RowExtractor()
        rv = e.extract('<p></p>', '//p')
        self.assertTrue(isinstance(rv, collections.Iterable))

    def test_extract_extracts_items(self):
        e = RowExtractor()
        doc = '<div><p class="a">One</p><p class="a">Two</p><p class="b">Three</p></div>'
        rv = e.extract(doc, "//p[@class='a']")
        self.assertEqual(len(rv), 2)


class UtilsTestCase(unittest.TestCase):
    def test_ensure_element_returs_htmlelement(self):
        doc = '<p>test</p>'
        elem = lxml.html.fromstring(doc)
        self.assertIsInstance(ensure_element(doc), lxml.html.HtmlElement)
        self.assertIsInstance(ensure_element(elem), lxml.html.HtmlElement)

    def test_scalar_returns_1st_elem_only(self):
        rv = self.assertEquals(scalar(['a','b']), 'a')
