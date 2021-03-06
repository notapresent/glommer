"""Low-level html parsing primitives"""

from string import ascii_uppercase, ascii_lowercase
import re
import lxml.html
from lxml.etree import XMLSyntaxError, XPathEvalError, ParserError
from urllib.parse import urljoin

RE_NS = "http://exslt.org/regular-expressions"  # this is the namespace for the EXSLT extensions

IMAGE_EXTENSIONS = ['jpeg', 'jpg', 'jpe', 'webp', 'png']
VIDEO_EXTENSIONS = ['avi', 'qt', 'mov', 'wmv', 'mpg', 'mpeg', 'mp4', 'webm']
STREAMING_EXTENSIONS = ['mp4', 'webm', 'flv', 'mov']


class ParseError(Exception):
    """Something unexpected happened while parsing html"""


class RowExtractor:

    """Extracts sequence of document fragments from document or fragment"""

    def __init__(self, *, selector):
        self.selector = selector

    def extract(self, doc_or_tree, base_url='.'):
        try:
            etree = ensure_element(doc_or_tree, base_url)
            return etree.xpath(self.selector, namespaces={'re': RE_NS})

        except (XMLSyntaxError, XPathEvalError) as e:
            raise ParseError(str(e)) from e


class FieldExtractor(RowExtractor):

    """Extracts scalar value from document fragment"""

    def extract(self, fragment, base_url='.'):
        value = super(FieldExtractor, self).extract(fragment, base_url)
        return first_or_none(value)


class DatasetExtractor:

    """Extracts sequence of dicts from document"""

    def __init__(self, *, selector, fields):
        self.row_extractor = RowExtractor(selector=selector)
        self.field_extractors = {name: FieldExtractor(selector=fs) for name, fs in fields.items()}

    def extract(self, doc_or_tree, base_url='.'):
        rows = self.row_extractor.extract(doc_or_tree, base_url)
        return [self.extract_fields(row, base_url) for row in rows]

    def extract_fields(self, row, base_url):
        return {name: ex.extract(row, base_url) for name, ex in self.field_extractors.items()}


class ChannelExtractor(DatasetExtractor):

    """ Extracts rows from html document"""

    def __init__(self, *, row_selector, url_selector, title_selector, extra_selector=None):
        fields = {
            'url': url_selector,
            'title': title_selector,
        }

        if extra_selector is not None:
            fields['extra'] = extra_selector

        super(ChannelExtractor, self).__init__(selector=row_selector, fields=fields)

    @classmethod
    def from_channel(cls, channel):
        """Create instance from channel fields"""
        param_names = ['row_selector', 'url_selector', 'title_selector', 'extra_selector']
        params = {param: getattr(channel, param) or None for param in param_names}
        return cls(**params)


class EntryExtractor:
    """Aggregates multiple extractors to operate on a single entry"""

    _instance = None

    def __init__(self):
        self._images_extractor = link_extractor(IMAGE_EXTENSIONS)
        self._videos_extractor = link_extractor(VIDEO_EXTENSIONS)
        self._streaming_extractor = RegexExtractor(STREAMING_EXTENSIONS)

    def extract(self, doc, base_url='.'):
        etree = ensure_element(doc, base_url)
        image_urls = [row['url'] for row in self._images_extractor.extract(etree, base_url)]
        video_urls = [row['url'] for row in self._videos_extractor.extract(etree, base_url)]
        streaming_urls = self._streaming_extractor.extract(doc, base_url)

        return {
            'images': image_urls,
            'videos': video_urls,
            'streaming': streaming_urls
        }

    @classmethod
    def extract_items(cls, doc, base_url='.'):      # TODO refactor this
        try:
            return cls._instance.extract(doc, base_url)
        except AttributeError:
            cls._instance = cls()
            return cls._instance.extract(doc, base_url)


class RegexExtractor:

    """Extracts text fragment from document using regular expression"""

    def __init__(self, extensions):
        ext_frag = '\.(?:%s)' % '|'.join(extensions)
        self._ext_rx = re.compile('([\w\.\-\/]+%s)' % ext_frag, re.IGNORECASE)

    def extract(self, doc, base_url='.'):
        return [urljoin(base_url, url) for url in self._ext_rx.findall(doc)]


def first_or_none(scalar_or_seq):
    """Returns first element if argument is a sequence, or argument itself if it is not iterable"""
    if isinstance(scalar_or_seq, str):
        return scalar_or_seq

    try:
        return next(iter(scalar_or_seq), None)

    except TypeError:
        return scalar_or_seq


def ensure_element(doc_or_tree, base_url='.'):
    """Returns lxml.html.HtmlElement, creates it from string if necessary"""
    if isinstance(doc_or_tree, lxml.html.HtmlElement):
        return doc_or_tree

    try:
        tree = lxml.html.fromstring(doc_or_tree, base_url=base_url)
        tree.make_links_absolute(resolve_base_href=True)    # TODO handle_failures='ignore'?
        return tree

    except (ValueError, TypeError, ParserError, XMLSyntaxError) as e:
        message = 'Invalid document {} - {!r}'.format(type(doc_or_tree), e)
        raise ParseError(message) from e


def xpath_tolower(what):
    """Uses XPath 1.0 translate() to emulate XPAth 2.0 lower-case()"""

    return "translate({}, '{}', '{}')".format(what, ascii_uppercase, ascii_lowercase)


def link_extractor(extensions):
    """Create extractor that extracts direct links to files (images, video, etc)"""
    href_nocase = xpath_tolower('@href')
    ext_fragment = ext_selector_fragment(href_nocase, extensions)
    selector = "//a[%s]//img[@src]" % ext_fragment      # XXX Do we really need thumbnails?

    return DatasetExtractor(
        selector=selector,
        fields={'url': 'ancestor::a/@href'}
    )


def ext_selector_fragment(what, extensions):
    """XPath selector fragment to match filenames with given extensions"""
    ext_rx = '\.({})'.format('|'.join(extensions))
    return "re:test({}, '{}')".format(what, ext_rx)     # XXX Maybe only match things *ending* with extension
