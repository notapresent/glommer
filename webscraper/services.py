from .models import Channel, Entry

class Scraper:
    def run(self):
        raise NotImplementedError()


class URLTracker:

    def __init__(self, channel):
        self.channel = channel

    def track(self, new_urls):
        urls_to_ids = self.get_current_urls_to_ids()
        add_urls, remove_urls = list_diff(urls_to_ids.keys(), new_urls)
        ids_to_remove = [urls_to_ids[url] for url in remove_urls]
        self.bulk_remove(ids_to_remove)
        return add_urls, remove_urls

    def bulk_remove(self, ids):
        Entry.objects.delete_from_channel_by_ids(self.channel, ids)

    def get_current_urls_to_ids(self):
        rows = Entry.objects.get_id_url_for_channel(self.channel)
        return {row['url']: row['id'] for row in rows}

def list_diff(old, new):
    oldset = set(old)
    newset = set(new)
    return newset - oldset, oldset - newset
