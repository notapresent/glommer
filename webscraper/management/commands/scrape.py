from django.core.management.base import BaseCommand, CommandError
from webscraper.services import Scraper


class Command(BaseCommand):
    help = 'Runs scrape tasks for channels'
    requires_migrations_checks = True

    def add_arguments(self, parser):
        pass    # TODO add interval argument. See https://docs.python.org/3/library/argparse.html#module-argparse

    def handle(self, *args, **options):
        robbo = Scraper()
        num_channels = robbo.run()
        self.stdout.write(self.style.SUCCESS('Scraped %d channels' % num_channels))
