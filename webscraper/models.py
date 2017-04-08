from django.contrib.postgres.fields import JSONField
from django.db.models import (Model, CharField, DateTimeField, ForeignKey, URLField, CASCADE, BooleanField,
                              IntegerField)
from django.utils.crypto import get_random_string

from .managers import ChannelManager, EntryManager


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

    ST_NEW = 0
    ST_OK = 1
    ST_WARNING = 2
    ST_ERROR = 3

    STATUS_CHOICES = (
        (ST_NEW, 'New'),
        (ST_OK, 'Ok'),
        (ST_WARNING, 'Warning'),
        (ST_ERROR, 'Error')
    )

    title = CharField(max_length=512)
    interval = CharField(max_length=3, choices=INTERVAL_CHOICES, default=I_1DAY)
    enabled = BooleanField(default=True)
    url = URLField(max_length=2048)
    slug = CharField(max_length=32, editable=False, null=False, unique=True)
    status = IntegerField(null=False, default=ST_NEW, choices=STATUS_CHOICES)

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


class Entry(Model):
    """Represents content entry"""

    ST_NEW = 0
    ST_OK = 1
    ST_WARNING = 2
    ST_ERROR = 3

    STATUS_CHOICES = (
        (ST_NEW, 'New'),
        (ST_OK, 'Ok'),
        (ST_WARNING, 'Warning'),
        (ST_ERROR, 'Error')
    )

    channel = ForeignKey(Channel, on_delete=CASCADE)
    added = DateTimeField('date added', auto_now_add=True)
    status = IntegerField(null=False, default=ST_NEW, choices=STATUS_CHOICES)
    url = URLField(max_length=2048)  # url as seen in channel
    title = CharField(max_length=512)
    extra = CharField(max_length=2048, blank=True)

    final_url = URLField(max_length=2048, blank=True)   # url after all redirects etc, blank if no redirects

    # {'media_type_1': ['url 1', 'url 2', ], 'media_type_2': ['url1', ...], ...}
    items = JSONField(default=None, null=True, blank=True)

    objects = EntryManager()

    @property
    def real_url(self):
        return self.final_url if self.final_url else self.url

    def __str__(self):
        return self.title
