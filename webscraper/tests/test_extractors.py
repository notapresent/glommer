import unittest

import lxml.html

from webscraper.extractors import (FieldExtractor, RowExtractor, DatasetExtractor, ensure_element, scalar,
                                   EntryExtractor, xpath_tolower, ext_selector_fragment, ParseError)


class FieldExtractorTestCase(unittest.TestCase):

    def setUp(self):
        self.extractor = FieldExtractor(selector='//a/text()')

    def test_extract_extracts(self):
        rv = self.extractor.extract('<a>some text</a>')
        self.assertEqual(rv, 'some text')

    def test_extract_accepts_lxml_htmlelement(self):
        elem = '<a>test text</a>'
        rv = self.extractor.extract(elem)
        self.assertEqual(rv, 'test text')

    def test_extract_returns_1st_element_only(self):
        rv = self.extractor.extract('<p><a>One</a><a>Two</a>')
        self.assertEqual(rv, 'One')

    def test_regexp_selector(self):
        self.extractor = FieldExtractor(selector="//a[re:test(@href, '\.(jpg|png)$')]/@href")
        self.assertEqual(self.extractor.extract('<a href="1.jpg">1</a>'), '1.jpg')
        self.assertEqual(self.extractor.extract('<a href="/dir/2.png">2</a>'), '/dir/2.png')

    def test_ext_selector_fragment(self):
        doc = '<img src="1.png"><img src="2.bmp"><img src="3.jpg">'
        frag = ext_selector_fragment('@src', ['jpg', 'png'])
        selector = '//img[{}]/@src'.format(frag)
        ex = RowExtractor(selector=selector)
        rv = ex.extract(doc)
        self.assertEqual(len(rv), 2)
        self.assertIn('1.png', rv)
        self.assertIn('3.jpg', rv)


class RowExtractorTestCase(unittest.TestCase):

    def test_extract_extracts_items(self):
        e = RowExtractor(selector="//p[@class='a']")
        doc = '<div><p class="a">One</p><p class="a">Two</p><p class="b">Three</p></div>'
        rv = e.extract(doc)
        self.assertEqual(len(rv), 2)
        self.assertEqual(rv[0].text, 'One')
        self.assertEqual(rv[1].text, 'Two')

    def test_extractor_raises_on_invalid_doc(self):
        e = RowExtractor(selector="//p[@class='a']")
        with self.assertRaises(ParseError):
            e.extract('')


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

    def test_ensure_element_raises_on_invalid_doc(self):
        with self.assertRaises(ParseError):
            ensure_element(None)

    def test_scalar_returns_1st_elem_only(self):
        rv = self.assertEqual(scalar(['a', 'b']), 'a')

    def test_xpath_tolower(self):
        rv = xpath_tolower('@href')
        self.assertEqual(rv, "translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')")


class EntryExtractorTestCase(unittest.TestCase):
    def test_entry_extractor_uses_same_tree(self):

        class ExtractorStub:
            def __init__(self):
                self.extract_args = []

            def extract(self, doc_or_tree):
                self.extract_args.append(doc_or_tree)

        e1, e2  =  ExtractorStub(), ExtractorStub()
        entry_extractor = EntryExtractor()
        entry_extractor.add_extractor('1', e1)
        entry_extractor.add_extractor('2', e2)
        entry_extractor.extract('<xml></xml>')
        self.assertEqual(e1.extract_args, e2.extract_args)
