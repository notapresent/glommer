from django.test import TestCase

from webscraper.admin import ChannelAdminForm, entry_title_with_link, entry_site, channel_feed_link
from webscraper.models import Channel, Entry
from .util import CHANNEL_DEFAULTS


class ChannelAdminFormTestCase(TestCase):

    def test_slug_field_disabled(self):
        form = ChannelAdminForm()
        slug_field = form.fields['slug']
        self.assertTrue(slug_field.disabled)


class AdminHelpersTestCase(TestCase):

    def test_entry_title_with_link(self):
        e = Entry(title='blah', url='http://host.com')
        rv = entry_title_with_link(e)
        self.assertIn(e.title, rv)
        self.assertIn(e.url, rv)

    def test_entry_site(self):
        e = Entry(url='http://somehost.com/doc.html')
        rv = entry_site(e)
        self.assertIn('somehost.com', rv)

    def test_channe_feed_link(self):
        c = Channel(**CHANNEL_DEFAULTS)
        c.save()    # slug generated on first save
        rv = channel_feed_link(c)
        self.assertIn(c.slug, rv)
