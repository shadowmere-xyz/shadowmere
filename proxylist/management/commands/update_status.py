from django.core.management.base import BaseCommand

from proxylist.tasks import update_status


class Command(BaseCommand):
    help = 'Update the status of the proxy list'

    def handle(self, *args, **options):
        update_status()
