from django.core.management.base import BaseCommand
from django.db import IntegrityError

from proxylist.models import Proxy, get_sip002


class Command(BaseCommand):
    help = "Cleanup proxy URLs"

    def handle(self, *args, **options):
        proxies = Proxy.objects.all()
        modified_count = 0

        for proxy in proxies:
            cleaned_url = get_sip002(proxy.url)
            if cleaned_url != proxy.url:
                proxy.url = cleaned_url
                try:
                    proxy.save()
                    modified_count += 1
                except IntegrityError:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Deleted duplicate proxy {proxy.id} with URL: {cleaned_url}"
                        )
                    )
                    proxy.delete()
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Error saving proxy {proxy.id} with cleaned URL: {e}"
                        )
                    )

        self.stdout.write(self.style.SUCCESS(f"Cleaned up {modified_count} proxies."))
