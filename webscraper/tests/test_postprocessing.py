import unittest

from webscraper.postprocessing import (highest_resolution, highest_res_from_group, group_by_resolution,
                                       postprocess_urlset, postprocess_items, deduplicate_urlsets)


class HighestResolutionTestCase(unittest.TestCase):

    def test_groups_by_same_url(self):
        urls = [
            'http://host.com/path/79296_sd_480p.mp4',
            'http://host.com/path/79296_sd_360p.mp4'
        ]
        rv = highest_resolution(urls)
        self.assertEquals(rv, [urls[0]])

    def test_leaves_varying_urls_as_is(self):
        urls = [
            'http://host.com/path/file1_sd_480p.mp4',
            'http://host.com/path/file2_sd_360p.mp4'
        ]
        rv = highest_resolution(urls)
        self.assertEquals(len(rv), 2)


class UrlPostprocessingTestCase(unittest.TestCase):

    def test_postprocess_urlset_strips_whitespace(self):
        rv = postprocess_urlset([' http://host.com/1 '], '')
        self.assertEqual(rv, ['http://host.com/1'])

    def test_postprocess_urlset_returns_absolute_urls(self):
        rv = postprocess_urlset(['1.jpg'], 'http://host.com')
        self.assertEqual(rv, ['http://host.com/1.jpg'])

    def test_deduplicate_deduplicates(self):
        items = {
            'one': [1, 2],
            'two': [2, 3]
        }
        deduplicate_urlsets(items)
        self.assertEqual(len(set(items['one']).intersection(items)), 0)

    def test_postprocess_items_removes_empty_sets(self):
        items = {
            'streaming': [],
            'images': ['1.jpg']
        }
        rv = postprocess_items(items)
        self.assertEquals(list(rv.keys()), ['images'])

    def test_postprocess_items_removes_lowres_versions(self):
        items = {
            'streaming': ['file_sd_480p', 'file_sd_360p']
        }
        rv = postprocess_items(items)
        self.assertEquals(rv['streaming'], ['file_sd_480p'])
