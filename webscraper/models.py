from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db.models import Model, CharField, DateTimeField, ForeignKey, URLField, CASCADE, BooleanField
from django.utils.crypto import get_random_string

from .managers import ChannelManager

class Channel(Model):
    """Represents content channel"""
    I_MANUAL = 'MAN'
    I_10MIN = '10M'
    I_1HOUR = '1H'
    I_1DAY = '1D'

    INTERVAL_CHOICES = (
        (I_MANUAL, 'Manual'),
        (I_10MIN, 'Every 10 minutes'),
        (I_1HOUR, 'Every hour'),
        (I_1DAY, 'Every day'),
    )

    title = CharField(max_length=512)
    interval = CharField(max_length=3, choices=INTERVAL_CHOICES, default=I_1DAY)
    enabled = BooleanField(default=True)
    url = URLField(max_length=2048)
    slug = CharField(max_length=32, editable=False, null=False, unique=True)

    row_selector = CharField(max_length=512)
    url_selector = CharField(max_length=512)
    title_selector = CharField(max_length=512)
    extra_selector = CharField(max_length=512, blank=True)

    objects = ChannelManager()

    @classmethod
    def make_slug(cls):
        while True:
            slug = get_random_string(length=32)
            if not cls.objects.filter(slug=slug).exists():
                break
        return slug

    def save(self, *args, **kwargs):
        if not self.id:     # new channel
            self.slug = Channel.make_slug()

        super(Channel, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    def extractor_settings(self):
        rv = {
            'selector': self.row_selector,
            'fields': {
                'url': {'selector': self.url_selector},
                'title': {'selector': self.title_selector},
            }
        }

        if self.extra_selector:
            rv['fields']['extra'] = {'selector': self.extra_selector}

        return rv

class Entry(Model):
    """Represents content entry"""
    channel = ForeignKey(Channel, on_delete=CASCADE)
    added = DateTimeField('date added', auto_now_add=True)

    url = URLField(max_length=2048)  # url as seen in channel
    title = CharField(max_length=512)
    extra = CharField(max_length=2048, blank=True)

    final_url = URLField(max_length=2048, blank=True)   # url after all redirects etc
    items = JSONField(default=None, null=True, blank=True)        # TODO: Document this structure

    def __str__(self):
        return self.title
