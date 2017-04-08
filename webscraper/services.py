from .models import Entry


class URLTracker:       # TODO move this to EntryManager

    """Keeps track of processed URLs"""

    def __init__(self, channel):
        self.channel = channel

    def track(self, entries):
        urls_to_ids = self.get_current_urls_to_ids()
        urls_to_entries = {e.url: e for e in entries}
        add_urls, remove_urls = list_diff(urls_to_ids.keys(), urls_to_entries.keys())
        ids_to_remove = [urls_to_ids[url] for url in remove_urls]
        self.bulk_remove(ids_to_remove)
        return [urls_to_entries.get(u) for u in add_urls]

    def bulk_remove(self, ids):
        Entry.objects.delete_from_channel_by_ids(self.channel, ids)

    def get_current_urls_to_ids(self):
        rows = Entry.objects.get_id_url_for_channel(self.channel)
        return {row['url']: row['id'] for row in rows}


def list_diff(old, new):
    oldset = set(old)
    newset = set(new)
    return newset - oldset, oldset - newset
