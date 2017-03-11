from django.db import models


class ChannelManager(models.Manager):
    def enabled(self):
        return super(ChannelManager, self).get_queryset().filter(enabled=True)


class EntryManager(models.Manager):
    def get_id_url_for_channel(self, channel):
        return super(EntryManager, self).get_queryset().values('id', 'url').filter(channel=channel)

    def delete_from_channel_by_ids(self, channel, ids):
        return super(EntryManager, self).get_queryset().filter(channel=channel, id__in=ids).delete()
