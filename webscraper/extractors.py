import lxml.html


class FieldExtractor:
    """Extracts scalar value from document fragment"""
    def __init__(self, **settings):
        self.selector = settings.pop('selector')

    def extract(self, fragment):
        fragment = ensure_element(fragment)

        results = fragment.xpath(self.selector)

        return scalar(results)


class RowExtractor:
    """Extracts sequence of document fragments from document or fragment"""
    def __init__(self, **settings):
        self.selector = settings.pop('selector')

    def extract(self, doc_or_tree):
        return ensure_element(doc_or_tree).xpath(self.selector)


def ensure_element(doc_or_tree):
    if isinstance(doc_or_tree, str):
        return lxml.html.fromstring(doc_or_tree)
    return doc_or_tree


def scalar(scalar_or_seq):
    try:
        return scalar_or_seq[0]
    except IndexError:
        return scalar_or_seq
