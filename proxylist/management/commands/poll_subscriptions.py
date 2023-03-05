from django.core.management.base import BaseCommand

from proxylist.tasks import update_status, poll_subscriptions


class Command(BaseCommand):
    help = "Poll all subscriptions looking for new keys"

    def handle(self, *args, **options):
        poll_subscriptions()
