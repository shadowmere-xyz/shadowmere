from apps.proxylist.tasks import poll_subscriptions
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Poll all subscriptions looking for new keys"

    def handle(self, *args, **options):
        poll_subscriptions()
