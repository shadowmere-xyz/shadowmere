import base64

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django_prometheus.models import ExportModelOperationsMixin

from proxylist.base64_decoder import decode_base64
from proxylist.proxy import update_proxy_status


class Proxy(ExportModelOperationsMixin('proxy'), models.Model):
    url = models.CharField(max_length=1024, unique=True)
    location = models.CharField(max_length=100, default="")
    is_active = models.BooleanField(default=False)
    last_checked = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(blank=True, default=now)

    def __str__(self):
        return f"{self.location} ({self.url})"


@receiver(post_save, sender=Proxy)
def convert_to_sip002_uri_scheme(sender, instance, created, **kwargs):
    if "#" in instance.url:
        instance.url = instance.url.split("#")[0]
    if "@" not in instance.url:
        url = instance.url.replace("ss://", "")

        decoded_url = decode_base64(url.encode('ascii'))
        encoded_bits = base64.b64encode(decoded_url.split(b"@")[0]).decode("ascii").rstrip("=")
        instance.url = f'ss://{encoded_bits}@{decoded_url.split(b"@")[1].decode("ascii")}'
        instance.save()


@receiver(post_save, sender=Proxy)
def save_location(sender, instance, created, **kwargs):
    if instance.location == "":
        update_proxy_status(instance)
