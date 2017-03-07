from webscraper.models import Channel, Entry


CHANNEL_DEFAULTS = {
    'title': 'Channel title',
    'interval': Channel.INTERVAL_CHOICES[0][0],
    'enabled': True,
    'url': 'http://example.com/',
    'row_selector': 'dummy selector',
    'url_selector': 'dummy selector',
    'title_selector': 'dummy selector',
    'extra_selector': 'dummy selector'
}

ENTRY_DEFAULTS = {
    'url': 'http://example.com/',
    'title': 'Test entry title',
    'extra': '',
    'final_url': '',
    'items': None,
}


def create_channel(**override_fields):
    fields = CHANNEL_DEFAULTS.copy()
    fields.update(override_fields)
    return Channel.objects.create(**fields)


def create_entry(**override_fields):
    fields = ENTRY_DEFAULTS.copy()
    fields.update(override_fields)
    fields.setdefault('channel', create_channel())
    return Entry.objects.create(**fields)
