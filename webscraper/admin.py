from urllib.parse import urlparse

from django import forms
from django.contrib import admin
from .models import Channel, Entry
from django.contrib.postgres.fields import JSONField
from prettyjson import PrettyJSONWidget
from django.utils.html import format_html
from django.urls import reverse


class JsonAdmin(admin.ModelAdmin):
    formfield_overrides = {
        JSONField: {'widget': PrettyJSONWidget}
    }


class ChannelAdminForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = [
            'title', 'url', 'enabled', 'interval', 'slug', 'status', 'row_selector', 'url_selector',
            'title_selector', 'extra_selector']

    def __init__(self, *args, **kwargs):
        super(ChannelAdminForm, self).__init__(*args, **kwargs)
        self.fields['slug'].disabled = True
        instance = getattr(self, 'instance', None)
        if not instance or not instance.pk:
            self.fields['slug'].required = False


def entry_title_with_link(entry):
    return format_html('<a target="_blank" href="{}">{}</a>', entry.real_url, entry.title)


def entry_site(entry):
    parsed = urlparse(entry.real_url)
    return format_html('<a href="{}://{}" target="_blank">{}</a>', parsed.scheme, parsed.netloc, parsed.netloc)


def channel_feed_link(channel):
    link = reverse('feed', kwargs={'channel_slug': channel.slug})
    return format_html('<a href="{}" target="_blank">feed</a>', link)


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    readonly_fields = (channel_feed_link,)

    list_display = ('title', 'enabled', channel_feed_link, 'status')
    list_filter = ['status', 'enabled', 'interval']
    fieldsets = [
        ('Feed link', {'fields': [channel_feed_link]}),
        ('Settings', {'fields': ['title', 'url', 'enabled', 'interval', 'slug', 'status']}),
        ('Selectors', {'fields': ['row_selector', 'url_selector', 'title_selector', 'extra_selector']}),
    ]
    form = ChannelAdminForm


@admin.register(Entry)
class EntryAdmin(JsonAdmin):
    date_hierarchy = 'added'
    list_display = ('id', entry_title_with_link, 'added', entry_site, 'status')
    list_filter = ['channel', 'status']
    search_fields = ['title', 'url', 'final_url']
    ordering = ('-added', )
