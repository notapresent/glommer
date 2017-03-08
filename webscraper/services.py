import os
import hashlib

import requests

from .models import Channel, Entry


class Scraper(object):
    def run(self):
        return 0    # TODO implement this


class Downloader:
    """Sequential downloader for testing"""
    def __init__(self, cache_dir=None):
        self._jobs = []
        if cache_dir:
            self._cache_dir = os.path.join(os.getcwd(), cache_dir)
        else:
            self._cache_dir = None

    def add_job(self, url, cb):
        self._jobs.append((url, cb))

    def run(self):
        for url, cb in self._jobs:
            text = self.get_cached(url)
            cb(text)

    def get(self, url):
        resp = requests.get(url)

        if resp.ok:
            return resp.text

        return None

    def get_cached(self, url):
        if not self._cache_dir:
            return self.get(url)

        filename = self.cached_filename(url)

        if os.path.isfile(filename):
            with open(filename, 'r') as f:
                return f.read()
        else:
            response = self.get(url)

        if response:
            with open(filename, 'w') as f:
                f.write(response)

        return response

    def cached_filename(self, url):
        md5 = hashlib.md5(url.encode('utf-8'))
        filename = md5.hexdigest()
        return os.path.join(self._cache_dir, filename)


class URLTracker:
    def __init__(self, channel):
        self.channel = channel

    def track(self, new_urls):
        add_urls, remove_urls = list_diff(self.current_urls(), new_urls)
        self.bulk_remove(remove_urls)
        return add_urls, remove_urls

    def bulk_remove(self, urls):
        Entry.objects.filter(channel=self.channel, url__in=urls).delete()

    def current_urls(self):
        rows = Entry.objects.filter(channel=self.channel).values('url')
        return [row['url'] for row in rows]


def list_diff(old, new):
    oldset = set(old)
    newset = set(new)
    return newset - oldset, oldset - newset
