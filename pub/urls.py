from django.conf.urls import url
from .feeds import ChannelFeed


urlpatterns = [
    url(r'^feeds/(?P<channel_slug>[a-zA-Z0-9]{32})/rss/$', ChannelFeed()),
]
