import unittest

import lxml.html

from webscraper.extractors import (FieldExtractor, RowExtractor, DatasetExtractor, ensure_element, scalar,
                                   MultiExtractor, xpath_tolower, ext_selector_fragment, make_video_extractor,
                                   make_images_extractor, make_entry_extractor)


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

    def test_regexp_selector(self):
        self.extractor = FieldExtractor(selector="//a[re:test(@href, '\.(jpg|png)$')]/@href")
        self.assertEqual(self.extractor.extract('<a href="1.jpg">1</a>'), '1.jpg')
        self.assertEqual(self.extractor.extract('<a href="/dir/2.png">2</a>'), '/dir/2.png')


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

    def test_xpath_tolower(self):
        rv = xpath_tolower('@href')
        self.assertEqual(rv, "translate(@href, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')")


class EntryExtractorsTestCase(unittest.TestCase):
    def test_entry_extractor_uses_same_tree(self):

        class ExtractorStub:
            def __init__(self):
                self.extract_args = []

            def extract(self, doc_or_tree):
                self.extract_args.append(doc_or_tree)

        e1, e2  =  ExtractorStub(), ExtractorStub()
        entry_extractor = make_entry_extractor()
        entry_extractor.extract('<xml></xml>')
        self.assertEqual(e1.extract_args, e2.extract_args)

    def test_image_extractor_extracts(self):
        iex = make_images_extractor()
        doc = '<a href="1.JPEG"><img src="1tn.jpg"></a> <a href="2.png"><img src="2t.jpg"></a>'
        rv = iex.extract(doc)
        self.assertEqual(len(rv), 2)
        self.assertIn({'url': '1.JPEG'}, rv)
        self.assertIn({'url': '2.png'}, rv)

    def test_image_extractor_skips_non_images(self):
        doc = '<a href="dir.jpg/file.html"></a><img src="tn.jpg"></a>'
        iex = make_images_extractor()
        rv = iex.extract(doc)
        self.assertEqual(len(rv), 0)

    def test_image_extractor_skips_text_only_links(self):
        doc = '<a href="file.jpg"></a>No thumbnail here</a>'
        iex = make_images_extractor()
        rv = iex.extract(doc)
        self.assertEqual(len(rv), 0)

    def test_video_extractor_extracts(self):
        vex = make_video_extractor()
        doc = '<a href="1.avi"><img src="1tn.jpg"></a> <a href="2.Mpg"><img src="2t.jpg"></a>'
        rv = vex.extract(doc)
        self.assertEqual(len(rv), 2)
        self.assertIn({'url': '1.avi'}, rv)
        self.assertIn({'url': '2.Mpg'}, rv)
