import logging
from urllib.parse import urljoin
import re

from django.core.exceptions import ValidationError
from .aiohttpdownloader import DownloadError
from .extractors import ChannelExtractor, EntryExtractor, ParseError
from .models import Channel, Entry


COMMON_RESOLUTIONS = ['hd_720', 'sd_480', 'sd_360', 'sd_240']

res_rx = re.compile('^(?P<prefix>.+)(?P<res>{})(?P<suffix>.+)$'.format('|'.join(COMMON_RESOLUTIONS)), re.I)

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


def process_entry(entry, fut):
    try:
        resp, html = fut.result()
        entry.real_url = str(resp.url)
        populate_entry(entry, html) or None

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


def parse_channel(channel, base_url, html):
    """Generates sequence of entries from channel html"""
    selector_keys = ['row_selector', 'url_selector', 'title_selector', 'extra_selector']
    extractor = ChannelExtractor(**{k: getattr(channel, k) or None for k in selector_keys})

    rows = extractor.extract(html)

    for row in rows:
        row['url'] = urljoin(base_url, row['url'])

        try:
            row = normalize_channel_row(row)
            entry = Entry(channel=channel, **row)
            entry.clean_fields()
            yield entry

        except ValidationError as e:
            logger.info("Invalid row %r in channel %r" % (row, channel))


def populate_entry(entry, html):
    extracted = EntryExtractor.extract_items(html)

    # TODO START
    entry.items = {}
    for alias, item_set in extracted.items():

        if not item_set:
            continue

        item_set = normalize_item_set(item_set)
        entry.items[alias] = [urljoin(entry.real_url, url) for url in item_set]

    entry.items = postprocess_items(entry.items, entry.real_url)
    # TODO END

def normalize_channel_row(row):
    return {k: v.strip() if v else '' for k, v in row.items()}


def normalize_item_set(items):
    return set(map(str.strip, items))


def highest_resolution(urls):
    groups, ungrouped = group_by_resolution(urls)

    for group in groups.values():
        best = highest_res_from_group(group)
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
            all_groups[groupname][res] = url
        else:
            all_groups[groupname] = {res: url}

    # if there is only 1 element in gooup then move it to ungrouped
    valid_groups = {}
    for group_name, group in all_groups.items():
        if len(group) > 1:
            valid_groups[group_name] = group
        else:
            url, = group.values()
            ungrouped.append(url)

    return valid_groups, ungrouped


def postprocess_items(items, base_url):
    seen = set()
    rv = {}
    for cat_name, urls in items.items():
        rv[cat_name] = [url for url in urls if url not in seen]
        seen = seen | set(rv[cat_name])

    return rv
