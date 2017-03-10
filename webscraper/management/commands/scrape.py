from django.core.management.base import BaseCommand, CommandError
from webscraper.services import Scraper


class Command(BaseCommand):
    help = 'Runs scrape tasks for channels'
    requires_migrations_checks = True

    def handle(self, *args, **options):
        robbo = Scraper()
        num_channels, num_entries = robbo.run()
        self.stdout.write(self.style.SUCCESS('Processed %d entries from %d channels' % (num_entries, num_channels)))
