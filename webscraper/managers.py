from django.db import models


class ChannelManager(models.Manager):
    def enabled(self):
        return super(ChannelManager, self).get_queryset().filter(enabled=True)
