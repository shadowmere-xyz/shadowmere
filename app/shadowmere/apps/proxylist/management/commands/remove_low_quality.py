from apps.proxylist.tasks import (
    remove_low_quality_proxies,
)
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Remove proxies with low quality"

    def handle(self, *args, **options):
        remove_low_quality_proxies()
