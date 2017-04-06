
from urllib.parse import urljoin

from webscraper.models import Channel, Entry
from webscraper.extractors import DatasetExtractor, MultiExtractor, ext_selector_fragment


class ParseError(Exception):    # TODO move to extractor
    pass


def parse_channel(channel, html):
    ex = DatasetExtractor(**channel.extractor_settings())
    try:
        rows = ex.extract(html)

    except Exception as e:        # FIXME change this
        raise ParseError from e

    else:
        for row in rows:
            row['url'] = urljoin(channel.url, row['url'])
            e = Entry(channel=channel, **row)
            yield e


def process_channel(channel, html):
    print('Processing channel ', channel)
    try:
        entries = parse_channel(channel, html)

    # except DownloadError as e:
    #     pass    # channel.status = Channel.ST_ERROR

    except ParseError as e:
        return []   # channel.status = Channel.ST_ERROR

    else:
        # channel.status = Channel.ST_OK
        return entries


def process_entry(entry, html, multiextractor):
    print('E', entry.channel.id, entry.title)
    entry.items = parse_entry(entry, html, multiextractor)
    return entry


def parse_entry(entry, html, multiextractor):
    base_url = entry.final_url or entry.url
    item_sets = multiextractor.extract(html)
    # import pdb; pdb.set_trace()
    for alias, iset in item_sets.items():
        if iset:
            item_sets[alias] = [urljoin(str(base_url), str(url)) for url in iset]

    return item_sets
