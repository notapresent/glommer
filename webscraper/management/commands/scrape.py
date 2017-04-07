from django.core.management.base import BaseCommand, CommandError
from webscraper.models import Channel
from webscraper.aioscraper import scrape


class Command(BaseCommand):
    help = 'Runs scrape tasks for channels'
    requires_migrations_checks = True

    def handle(self, *args, **options):
        channels = Channel.objects.enabled()
        scrape(channels)
        msg = 'Processed {} channels'.format(len(channels))
        self.stdout.write(self.style.SUCCESS(msg))
