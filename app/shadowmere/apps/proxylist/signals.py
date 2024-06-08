import re

from apps.proxylist.models import Proxy
from django.core.cache import cache
from django.db import IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from utils.proxy import update_proxy_status
from utils.uri_scheme import get_sip002


@receiver(post_save, sender=Proxy)
def update_url_and_location_after_save(sender, instance, created, **kwargs):
    url = get_sip002(instance.url)
    if url != instance.url:
        instance.url = url
        instance.save()
        return

    if instance.port == 0:
        server_and_port = instance.url.split("@")[1]
        instance.port = int(re.findall(r":(\d+)", server_and_port)[-1])
        instance.save()
        return

    if instance.location == "":
        update_proxy_status(instance)
        try:
            instance.save()
        except IntegrityError:
            # This means the proxy is either a duplicate or no longer valid
            instance.delete()


@receiver(post_save, sender=Proxy)
def clear_cache(sender, instance, **kwargs):
    cache.clear()
