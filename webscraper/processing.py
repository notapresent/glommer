import logging

from django.core.exceptions import ValidationError

from .aiohttpdownloader import DownloadError
from .extractors import ChannelExtractor, EntryExtractor, ParseError
from .postprocessing import postprocess_items
from .models import Channel, Entry


logger = logging.getLogger(__name__)


def process_channel(channel, fut):
    """Set channel status, return sequence of new entries"""

    new_entries = []

    try:
        response, html = fut.result()
        base_url = str(response.url)
        entries = list(parse_channel(channel, base_url, html))

    except DownloadError as e:
        channel.status = Channel.ST_WARNING
        logger.warning('%r - %r' % (channel, e))

    except ParseError as e:
        channel.status = Channel.ST_ERROR
        logger.exception('%r - %r' % (channel, e))

    else:
        if entries:
            channel.status = Channel.ST_OK
            new_entries = Entry.objects.track_entries(channel, entries)
        else:
            channel.status = Channel.ST_WARNING
            logger.info('%r - no entries' % channel)

    return new_entries


def parse_channel(channel, base_url, html):
    """Generates sequence of entries from channel html"""
    extractor = ChannelExtractor.from_channel(channel)

    for row in extractor.extract(html, base_url):
        try:
            entry = Entry(channel=channel, **row)
            entry.clean_fields(exclude=['channel'])
            yield entry

        except ValidationError as e:
            logger.warning("Invalid row %r in channel %r" % (row, channel))


def process_entry(entry, fut):
    """Set entry status, populate entry.items"""
    try:
        resp, html = fut.result()
        entry.real_url = str(resp.url)
        items = parse_entry(entry.real_url, html)

    except (DownloadError, ParseError) as e:
        entry.status = Entry.ST_ERROR
        logger.info('%r - %r' % (entry, e))

    else:
        if items:
            entry.status = Entry.ST_OK
            entry.items = items

        else:
            entry.status = Entry.ST_WARNING
            logger.info('%r - No items' % (entry, ))

    return entry


def parse_entry(base_url, html):
    """Parse entry html, return sets of item urls"""
    extracted = EntryExtractor.extract_items(html, base_url)

    return postprocess_items(extracted)
