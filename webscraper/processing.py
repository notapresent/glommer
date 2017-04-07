from urllib.parse import urljoin

from webscraper.extractors import ParseError
from .aiohttpdownloader import DownloadError
from .extractors import DatasetExtractor, ext_selector_fragment, EntryExtractor
from .models import Entry
from .services import URLTracker

IMAGE_EXTENSIONS = ['jpeg', 'jpg', 'jpe', 'webp', 'png']
VIDEO_EXTENSIONS = ['avi', 'qt', 'mov', 'wmv', 'mpg', 'mpeg', 'mp4', 'webm']

STATIC_EXTRACTOR_SETTINGS = {
    'images': ('//a[', '@href', IMAGE_EXTENSIONS, ']/img[@src]'),
    'videos': ('//a[', '@href', VIDEO_EXTENSIONS, ']/img[@src]')
}


def process_channel(channel, fut):
    try:
        response, html = fut.result()
        entries = parse_channel(channel, response, html)

    except (DownloadError, ParseError) as e:
        pass    # channel.status = Channel.ST_ERROR
        return []

    else:
        tracker = URLTracker(channel)
        new_entries = tracker.track(entries)
        return new_entries
        # channel.status = Channel.ST_OK
        pass

    finally:
        pass
        # channel.save()
        print('C', channel.title, len(new_entries))


def process_entry(entry, fut, entry_extractor):
    print('E', entry.channel.id, entry.title)
    try:
        resp, html = fut.result()
        actual_url = str(resp.url)
        entry.final_url = actual_url if actual_url != entry.url else '' # TODO None
        items = parse_entry(entry, html, entry_extractor)

    except DownloadError as e:
        pass    # entry.status = Entry.ST_ERROR

    except ParseError as e:
        pass    # entry.status = Entry.ST_ERROR

    else:
        entry.items = normalize_entry_items(items)
        # entry.status = Entry.ST_OK if items else Entry.ST_WARN

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


def parse_channel(channel, resp, html):
    base_url = str(resp.url)
    extractor = make_channel_extractor(channel)
    rows = extractor.extract(html)

    for row in rows:
        row = normalize_channel_row(row)
        row['url'] = urljoin(base_url, row['url'])
        entry = Entry(channel=channel, **row)
        yield entry


def parse_entry(entry, html, entry_extractor):
    base_url = entry.final_url or entry.url
    item_sets = entry_extractor.extract(html)
    # import pdb; pdb.set_trace()
    for alias, iset in item_sets.items():
        if iset:
            item_sets[alias] = [urljoin(str(base_url), str(url)) for url in iset]

    return item_sets


def normalize_entry_items(items): # TODO
    return items

def normalize_channel_row(row): # TODO
    return row