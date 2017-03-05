import lxml.html


class RowExtractor:
    """Extracts sequence of document fragments from document or fragment"""
    def __init__(self, **settings):
        self.selector = settings.pop('selector')

    def extract(self, doc_or_tree):
        return ensure_element(doc_or_tree).xpath(self.selector)

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


def ensure_element(doc_or_tree):
    if isinstance(doc_or_tree, str):
        return lxml.html.fromstring(doc_or_tree)
    return doc_or_tree


def scalar(scalar_or_seq):
    try:
        return scalar_or_seq[0]
    except IndexError:
        return scalar_or_seq
