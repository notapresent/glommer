from django import forms
from django.contrib import admin
from .models import Channel, Entry


class ChannelAdminForm(forms.ModelForm):

    class Meta:
        model = Channel
        fields = ['title', 'url', 'enabled', 'interval', 'slug', 'status', 'row_selector', 'url_selector',
                  'title_selector', 'extra_selector']

    def __init__(self, *args, **kwargs):
        super(ChannelAdminForm, self).__init__(*args, **kwargs)
        self.fields['slug'].widget.attrs['readonly'] = True

        instance = getattr(self, 'instance', None)
        if not instance or not instance.pk:
            self.fields['slug'].widget = forms.HiddenInput()
            self.fields['slug'].required = False


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ('title', 'enabled', 'feed_link', 'status')
    list_filter = ['status', 'enabled', 'interval']
    fieldsets = [
        (None, {'fields': ['title', 'url', 'enabled', 'interval', 'slug', 'status']}),
        ('Selectors', {'fields': ['row_selector', 'url_selector', 'title_selector', 'extra_selector']}),
    ]
    form = ChannelAdminForm


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'added'
    list_display = ('id', 'title_with_link', 'added', 'site', 'status')
    list_filter = ['channel', 'status']
    search_fields = ['title', 'url', 'final_url']
    ordering = ('-added', )
