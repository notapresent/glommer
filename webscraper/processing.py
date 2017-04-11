import logging
from urllib.parse import urljoin

from django.core.exceptions import ValidationError
from webscraper.extractors import ParseError
from .aiohttpdownloader import DownloadError
from .extractors import DatasetExtractor, ext_selector_fragment, EntryExtractor
from .models import Channel, Entry

IMAGE_EXTENSIONS = ['jpeg', 'jpg', 'jpe', 'webp', 'png']
VIDEO_EXTENSIONS = ['avi', 'qt', 'mov', 'wmv', 'mpg', 'mpeg', 'mp4', 'webm']

STATIC_EXTRACTOR_SETTINGS = {
    'images': ('//a[', '@href', IMAGE_EXTENSIONS, ']/img[@src]'),
    'videos': ('//a[', '@href', VIDEO_EXTENSIONS, ']/img[@src]')
}


logger = logging.getLogger(__name__)


def process_channel(channel, fut):
    new_entries = []

    try:
        response, html = fut.result()
        base_url = str(response.url)
        entries = parse_channel(channel, base_url, html)

    except DownloadError as e:
        channel.status = Channel.ST_WARNING
        logger.warning('%r - %r' % (channel, e))

    except ParseError as e:
        channel.status = Channel.ST_ERROR
        logger.exception('%r - %r' % (channel, e))

    else:
        new_entries = Entry.objects.track_entries(channel, entries)
        channel.status = Channel.ST_OK
        logger.info('%r - %d new entries' % (channel, len(new_entries)))

    channel.save()
    return new_entries


def process_entry(entry, fut, entry_extractor):
    try:
        resp, html = fut.result()
        actual_url = str(resp.url)
        entry.final_url = actual_url if actual_url != entry.url else ''
        entry.items = parse_entry(entry, html, entry_extractor) or None
        ensure_entry_title(entry, html, entry_extractor)

    except (DownloadError, ParseError) as e:
        entry.status = Entry.ST_ERROR
        logger.info('%r - %r' % (entry, e))

    else:
        if entry.items:
            entry.status = Entry.ST_OK
            num_items = sum([len(urls) for urls in entry.items.values()])
            logger.info('%r - %d items' % (entry, num_items))
        else:
            entry.status = Entry.ST_WARNING
            logger.info('%r - No items' % (entry, ))

    return entry


def make_entry_extractor():
    """Creates and configures entry extractor"""
    ee = EntryExtractor()

    for alias, args in STATIC_EXTRACTOR_SETTINGS.items():
        ee.add_extractor(alias, make_static_extractor(*args))

    # TODO: add streaming extractor here

    return ee


def make_static_extractor(prefix, what, extensions, suffix):
    """Create extractor that extracts links to static files (images, video, etc)"""

    ext_fragment = ext_selector_fragment(what, extensions)
    selector = prefix + ext_fragment + suffix
    return DatasetExtractor(
        selector=selector,
        fields={'url': {'selector': 'parent::a/@href'}}
    )


def make_channel_extractor(channel):
    """Create extractor that extracts rows"""
    args = {
        'selector': channel.row_selector,
        'fields': {
            'url': {'selector': channel.url_selector},
            'title': {'selector': channel.title_selector},
        }
    }

    if channel.extra_selector:
        args['fields']['extra'] = {'selector': channel.extra_selector}

    return DatasetExtractor(**args)


def parse_channel(channel, base_url, html):
    """Generates sequence of entries from channel html"""
    extractor = make_channel_extractor(channel)
    rows = extractor.extract(html)

    for row in rows:
        row['url'] = urljoin(base_url, row['url'])

        try:
            entry = make_entry(row)
            entry.channel = channel
            yield entry

        except ValidationError as e:
            logger.info("Invalid row %r in channel %r" % (row, channel))

def make_entry(row):
    row = normalize_channel_row(row)
    entry = Entry(**row)
    entry.clean_fields(exclude=['channel', 'title'])    # we can set title from entry page if its empty
    return entry


def parse_entry(entry, html, entry_extractor):
    item_sets = entry_extractor.extract(html)

    rv = {}
    for alias, item_set in item_sets.items():

        if not item_set:
            continue

        url_set = normalize_item_set([i['url'] for i in item_set])
        rv[alias] = [urljoin(entry.real_url, url) for url in url_set]

    return rv


def normalize_channel_row(row):
    for k, v in row.items():
        row[k] = v.strip() if v else ''
    return row


def normalize_item_set(items):
    return set(map(str.strip, items))


def ensure_entry_title(entry, html, entry_extractor):
    if entry.title:
        return

    page_title = entry_extractor.extract_field('//title/text()', html)

    if not page_title:
        raise ParseError('Unable to extract title')

    entry.title = page_title.strip()
