import unittest

import lxml.html

from .fieldextractor import FieldExtractor


class FieldExtractorTestCase(unittest.TestCase):
    def test_extractor_exists(self):
        e = FieldExtractor({'selector': '//a/text()'})

    def test_it_extracts(self):
        e = FieldExtractor({'selector': '//a/text()'})
        rv = e.extract('<a>some text</a>')
        self.assertEqual(rv, 'some text')

    def test_it_accepts_lxml_elementtree(self):
        tree = lxml.html.fragment_fromstring('<a>test text</a>')
        e = FieldExtractor({'selector': '//a/text()'})
        self.assertEqual(e.extract(tree), 'test text')

    def test_it_returns_1st_element(self):
        e = FieldExtractor({'selector': '//a/text()'})
        rv = e.extract('<p><a>One</a><a>Two</a>')
        self.assertEqual(rv, 'One')

