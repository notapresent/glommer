from django.test import TestCase

from webscraper.admin import ChannelAdminForm
from webscraper.models import Channel


class ChannelAdminFormTestCase(TestCase):

    def test_slug_field_disabled(self):
        form = ChannelAdminForm()
        slug_field = form.fields['slug']
        self.assertTrue(slug_field.disabled)
