import timeit
import unittest


from .services import Downloader


class DownloaderTestCase(unittest.TestCase):
    def test_downloads(self):
        def cb(text):
            self.assertIn('origin', text)

        d = Downloader()
        d.add_job('https://httpbin.org/ip', cb)
        d.run()

    def test_cacing(self):
        url = 'https://httpbin.org/get?testheader=1'
        d = Downloader(cache_dir='.localdata/cache')
        d.add_job(url, lambda t: None)
        d.run()
        d.add_job(url, lambda t: self.assertIn('testheader', t))
        elapsed = timeit.timeit(d.run, number=1)
        self.assertLess(elapsed, 0.0001)
