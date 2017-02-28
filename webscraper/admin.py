from django.contrib import admin

# Register your models here.

from .models import Channel, ChannelExtractor, Entry

admin.site.register(Channel)
admin.site.register(ChannelExtractor)
admin.site.register(Entry)
