from django.core.management.base import BaseCommand

from proxylist.models import Proxy


class Command(BaseCommand):
    help = "Clear all quality statistics"

    def add_arguments(self, parser):
        parser.add_argument("times", type=int)

    def handle(self, *args, **options):
        times = int(options["times"])
        for proxy in Proxy.objects.all():
            proxy.times_checked = proxy.times_checked - times
            proxy.save()
