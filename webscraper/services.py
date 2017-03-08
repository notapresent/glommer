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

    def track(self, new_rowset):
        return []

    def query(self):
        return Entry.objects.filter(channel=self.channel).values('id', 'url')


def rowset_to_map(rowset, keyname):
    return {row[keyname]: row for row in rowset}


def rowset_diff(oldset, newset):
    old_url_to_rec = rowset_to_map(oldset, 'url')
    new_url_to_rec = rowset_to_map(newset, 'url')
    old_urlset = set(old_url_to_rec.keys())
    new_urlset = set(new_url_to_rec.keys())
    remove_urls = old_urlset - new_urlset

    add_urls = new_urlset - old_urlset

    return ([new_url_to_rec[url] for url in add_urls],
            [old_url_to_rec[url] for url in remove_urls])


