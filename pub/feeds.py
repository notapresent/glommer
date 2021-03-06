from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404
from django.template.loader import get_template, render_to_string
from webscraper.models import Channel, Entry


FEED_TTL = {
    Channel.I_1DAY: 1440,
    Channel.I_1HOUR: 60,
    Channel.I_10MIN: 10,
    Channel.I_MANUAL: 1440
}

class ChannelFeed(Feed):
    """Channel feed implementation"""
    # ttl = 1440 # 60 minutes * 24 hours  TODO: this should
    def ttl(self, channel):
        return FEED_TTL[channel.interval]


    def get_object(self, request, channel_slug):
        return get_object_or_404(Channel, slug=channel_slug)

    def title(self, channel):
        return channel.title

    def link(self, obj):
        return obj.url

    def description(self, channel):
        return "Latest entries from %s" % channel.title

    def items(self, channel):
        return Entry.objects.filter(channel=channel, status=1).order_by('-added')

    def item_link(self, entry):
        return entry.final_url or entry.url

    def item_title(self, entry):
        return entry.title

    def item_description(self, entry):
        ctx = {'entry': entry, 'itemsets': entry.items}
        return render_to_string('entry_description.html', ctx)
