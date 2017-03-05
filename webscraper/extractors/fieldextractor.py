"""FieldExtractor extracts scalar value from document fragment"""
import lxml.html


class FieldExtractor:
    def __init__(self, settings):
        self.selector = settings.pop('selector', None)

    def extract(self, fragment):
        if isinstance(fragment, str):
            fragment = lxml.html.fragment_fromstring(fragment)

        result = fragment.xpath(self.selector)

        if isinstance(result, list):
            result = result[0]

        return result

