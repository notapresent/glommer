"""Functions related to parsing entries and channels"""

from string import ascii_uppercase, ascii_lowercase

import lxml.html


RE_NS = "http://exslt.org/regular-expressions" # this is the namespace for the EXSLT extensions
IMAGE_EXTENSIONS = ['jpeg', 'jpg', 'jpe', 'webp', 'png']
VIDEO_EXTENSIONS = ['avi', 'qt', 'mov', 'wmv', 'mpg', 'mpeg', 'mp4', 'webm']


class RowExtractor:

    """Extracts sequence of document fragments from document or fragment"""

    def __init__(self, **settings):
        self.selector = settings.pop('selector')

    def extract(self, doc_or_tree):
        return ensure_element(doc_or_tree).xpath(self.selector, namespaces={'re':RE_NS})


class FieldExtractor(RowExtractor):

    """Extracts scalar value from document fragment"""

    def extract(self, fragment):
        value = super(FieldExtractor, self).extract(fragment)
        return scalar(value)


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


class MultiExtractor:

    """Set of extractors to operate on a single document"""

    def __init__(self):
        self.extractors = {}

    def add_extractor(self, alias, extractor):
        self.extractors[alias] = extractor

    def extract(self, doc_or_tree):
        tree = ensure_element(doc_or_tree)
        return {alias: e.extract(tree) for alias, e in self.extractors.items()}


def ensure_element(doc_or_tree):
    if isinstance(doc_or_tree, str):
        return lxml.html.fromstring(doc_or_tree)
    return doc_or_tree


def scalar(scalar_or_seq):
    try:
        return scalar_or_seq[0]
    except IndexError:
        return scalar_or_seq


def xpath_tolower(what):

    """Uses XPath 1.0 translate() to emulate XPAth 2.0 lower-case()"""

    return "translate({}, '{}', '{}')".format(what, ascii_uppercase, ascii_lowercase)


def ext_selector_fragment(what, extensions):

    """XPath selector fragment to match filenames"""

    what = xpath_tolower(what)
    rx = extensions_regex(extensions)
    return "re:test({}, '{}')".format(what, rx)


def extensions_regex(extensions):

    """Regex to math certain filetypes"""

    return '\.({})$'.format('|'.join(extensions))


def make_entry_extractor():
    me = MultiExtractor()
    me.add_extractor('images', make_images_extractor())
    me.add_extractor('video', make_video_extractor())
    return me


def make_images_extractor():
    fragment = ext_selector_fragment('@href', IMAGE_EXTENSIONS)
    images_selector = '//a[{}]/img[@src]'.format(fragment)
    return DatasetExtractor(
        selector=images_selector,
        fields={'url': {'selector': 'parent::a/@href'}}
    )


def make_video_extractor():
    fragment = ext_selector_fragment('@href', VIDEO_EXTENSIONS)
    video_selector = '//a[{}]/img[@src]'.format(fragment)
    return DatasetExtractor(
        selector=video_selector,
        fields={'url': {'selector': 'parent::a/@href'}}
    )
