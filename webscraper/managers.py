from django.db import models


class ChannelManager(models.Manager):

    """Table level operations for Channel model"""

    def enabled(self):
        return super(ChannelManager, self).get_queryset().filter(enabled=True)


class EntryManager(models.Manager):

    """Table level operations for Entry model"""

    def track_entries(self, channel, new_entries):
        """Deletes from DB entries that are not in in new_entries, returns entries that are not in DB"""
        new_url2entry = {entry.url: entry for entry in new_entries}
        existing_url2id = {r['url']: r['id'] for r in self.get_id_url_for_channel(channel)}
        new_urls = new_url2entry.keys() - existing_url2id.keys()
        old_urls = existing_url2id.keys() - new_url2entry.keys()
        self.delete_from_channel_by_ids(channel, [existing_url2id[url] for url in old_urls])
        return [new_url2entry[url] for url in new_urls]

    def get_id_url_for_channel(self, channel):
        return super(EntryManager, self).get_queryset().values('id', 'url').filter(channel=channel)

    def delete_from_channel_by_ids(self, channel, ids):
        return super(EntryManager, self).get_queryset().filter(channel=channel, id__in=ids).delete()
