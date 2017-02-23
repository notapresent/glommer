from django.db.models import Model, CharField, DateTimeField, ForeignKey, IntegerField, CASCADE
from django.contrib.postgres.fields import ArrayField, JSONField


class Channel(Model):
    """Represents content channel"""
    url = CharField(max_length=2048)
    selector = CharField(max_length=512)
    title = CharField(max_length=512)
    adapters = ArrayField(base_field=JSONField(), default=list)      # [{'adapter_name': {/* adapter settings*/}}, ...]


class Entry(Model):
    """Represents content entry"""
    channel = ForeignKey(Channel, on_delete=CASCADE)
    added = DateTimeField('date added')
    title = CharField(max_length=512)
    url = CharField(max_length=2048)    # url as seen in channel
    final_url = CharField(max_length=2048, null=True)   # url after all redirects etc, null if equals to original url
    items = JSONField(null=True)        # {'adapter_name': {/* items */}, ...}
