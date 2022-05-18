from django.core.management.base import BaseCommand

from proxylist.models import Proxy


class Command(BaseCommand):
    help = "Clear all quality statistics"

    def handle(self, *args, **options):
        for proxy in Proxy.objects.all():
            proxy.times_checked = 0
            proxy.times_check_succeeded = 0
            proxy.save()
