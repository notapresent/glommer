import logging
import re
from urllib.parse import urljoin, urlparse

from django.core.exceptions import ValidationError
from webscraper.extractors import ParseError
from .aiohttpdownloader import DownloadError
from .extractors import DatasetExtractor, ext_selector_fragment, EntryExtractor, RegexExtractor
from .models import Channel, Entry

IMAGE_EXTENSIONS = ['jpeg', 'jpg', 'jpe', 'webp', 'png']
VIDEO_EXTENSIONS = ['avi', 'qt', 'mov', 'wmv', 'mpg', 'mpeg', 'mp4', 'webm']
STREAMING_EXTENSIONS = ['mp4', 'webm', 'flv', 'mov']

STATIC_EXTRACTOR_SETTINGS = {
    'images': ('//a[', '@href', IMAGE_EXTENSIONS, ']/img[@src]'),
    'videos': ('//a[', '@href', VIDEO_EXTENSIONS, ']/img[@src]')
}

COMMON_RESOLUTIONS = ['hd_720', 'sd_480', 'sd_360', 'sd_240']

res_rx = re.compile('^(?P<prefix>.+)(?P<res>{})(?P<suffix>.+)$'.format('|'.join(COMMON_RESOLUTIONS)), re.IGNORECASE)
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
        ee.add_extractor(alias, make_static_extractor(*args), extractor_type='lxml')

    streaming_extractor = RegexExtractor(STREAMING_EXTENSIONS)
    ee.add_extractor('streaming', streaming_extractor, extractor_type='text')

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


def highest_resolution(urls):
    groups, ungrouped = group_by_resolution(urls)

    for group in groups.values():
        best = highest_res_from_group(group['versions'])
        ungrouped.append(best)

    return ungrouped


def highest_res_from_group(versions_dict):  # versions_dict == {resolution: url, ...}
    top_key = sorted(versions_dict.keys(), key=COMMON_RESOLUTIONS.index)[0]
    return versions_dict[top_key]


def group_by_resolution(urls):
    all_groups, ungrouped = {}, []

    for url in urls:
        matches = res_rx.fullmatch(url)

        if matches is None:
            ungrouped.append(url)
            continue

        prefix, res, suffix = matches.groups()
        groupname = prefix + suffix

        if groupname in all_groups:
            all_groups[groupname]['versions'][res] = url
        else:
            all_groups[groupname] = {
                'prefix': prefix,
                'suffix': suffix,
                'versions': {res: url}
            }

    # if there is only 1 element in gooup then move it to ungrouped
    valid_groups = {}
    for group_name, group in all_groups.items():
        if len(group['versions']) > 1:
            valid_groups[group_name] = group
        else:
            url, = group['versions'].values()
            ungrouped.append(url)

    return valid_groups, ungrouped
