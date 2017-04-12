"""Low-level html parsing primitives"""

from string import ascii_uppercase, ascii_lowercase
import re

import lxml.html
from lxml.etree import XMLSyntaxError, XPathEvalError, ParserError


RE_NS = "http://exslt.org/regular-expressions"  # this is the namespace for the EXSLT extensions


class RowExtractor:

    """Extracts sequence of document fragments from document or fragment"""

    def __init__(self, **settings):
        self.selector = settings.pop('selector')

    def extract(self, doc_or_tree):
        try:
            etree = ensure_element(doc_or_tree)
            return etree.xpath(self.selector, namespaces={'re': RE_NS})

        except (XMLSyntaxError, XPathEvalError) as e:
            raise ParseError() from e


class FieldExtractor(RowExtractor):

    """Extracts scalar value from document fragment"""

    def extract(self, fragment):
        value = super(FieldExtractor, self).extract(fragment)
        return first_or_none(value)


class DatasetExtractor:

    """Extracts sequence of dicts from document"""

    def __init__(self, **settings):
        self.row_extractor = RowExtractor(selector=settings.pop('selector'))
        self.set_fields(settings.pop('fields'))

    def set_fields(self, fields_settings):
        self.fields = {name: FieldExtractor(**fs) for name, fs in fields_settings.items()}

    def extract(self, doc_or_tree):
        rows = self.row_extractor.extract(doc_or_tree)
        return [self.extract_fields(row) for row in rows]

    def extract_fields(self, row):
        rv = {name: self.fields[name].extract(row) for name in self.fields.keys()}
        return rv


def ensure_element(doc_or_tree):
    if isinstance(doc_or_tree, lxml.html.HtmlElement):
        return doc_or_tree

    try:
        return lxml.html.fromstring(doc_or_tree)

    except (ValueError, TypeError, ParserError) as e:
        message = 'Invalid document {} - {!r}'.format(type(doc_or_tree), e)
        raise ParseError(message) from e


def first_or_none(scalar_or_seq):
    if isinstance(scalar_or_seq, str):
        return scalar_or_seq

    try:
        return next(iter(scalar_or_seq or []), None)

    except TypeError:
        return scalar_or_seq


def xpath_tolower(what):
    """Uses XPath 1.0 translate() to emulate XPAth 2.0 lower-case()"""

    return "translate({}, '{}', '{}')".format(what, ascii_uppercase, ascii_lowercase)


def ext_selector_fragment(what, extensions):
    """XPath selector fragment to match filenames"""

    what = xpath_tolower(what)
    ext_rx = '\.({})'.format('|'.join(extensions))
    return "re:test({}, '{}')".format(what, ext_rx)


class EntryExtractor:
    """Set of extractors to operate on a single document"""

    def __init__(self):
        self._lxml_extractors = {}
        self._text_extractors = {}

    def add_extractor(self, alias, extractor, extractor_type='lxml'):
        if extractor_type == 'lxml':
            self._lxml_extractors[alias] = extractor
        else:
            self._text_extractors[alias] = extractor

    def extract(self, doc):
        rv = {}
        etree = ensure_element(doc)

        for alias, ex in self._lxml_extractors.items():
            rv[alias] =  ex.extract(etree)

        for alias, ex in self._text_extractors:
            rv.setdefault(alias, [])
            rv[alias].extend(doc)

        return rv


    def extract_field(self, sel, doc):
        ex = FieldExtractor(selector=sel)
        elem = ensure_element(doc)
        return first_or_none(ex.extract(elem))


class ParseError(Exception):
    """Something unexpected happened while parsing html"""


class RegexExtractor:

    def __init__(self, extensions):
        ext_frag = '\.(?:%s)' % '|'.join(extensions)
        self._ext_rx = re.compile('([\w\.\-\/]+%s)' % ext_frag, re.IGNORECASE)

    def extract(self, doc):
        return self._ext_rx.findall(doc)
