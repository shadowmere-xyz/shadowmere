import base64

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django_prometheus.models import ExportModelOperationsMixin

from proxylist.base64_decoder import decode_base64
from proxylist.proxy import update_proxy_status


def validate_not_existing(value):
    if Proxy.objects.filter(url=get_sip002(value)):
        raise ValidationError(
            'This proxy was already imported',
            params={'value': value},
        )


class Proxy(ExportModelOperationsMixin('proxy'), models.Model):
    url = models.CharField(max_length=1024, unique=True, validators=[validate_not_existing, ])
    location = models.CharField(max_length=100, default="")
    is_active = models.BooleanField(default=False)
    last_checked = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(blank=True, default=now)

    def __str__(self):
        return f"{self.location} ({self.url})"


def get_sip002(instance_url):
    url = instance_url
    if "#" in url:
        url = url.split("#")[0]
    if "=" in url:
        url = url.replace("=", "")
    if "@" not in url:
        url = url.replace("ss://", "")

        decoded_url = decode_base64(url.encode('ascii'))
        encoded_bits = base64.b64encode(decoded_url.split(b"@")[0]).decode("ascii").rstrip("=")
        url = f'ss://{encoded_bits}@{decoded_url.split(b"@")[1].decode("ascii")}'

    return url


@receiver(post_save, sender=Proxy)
def convert_to_sip002_uri_scheme(sender, instance, created, **kwargs):
    url = get_sip002(instance.url)
    if url != instance.url:
        instance.url = url
        instance.save()


@receiver(post_save, sender=Proxy)
def save_location(sender, instance, created, **kwargs):
    if instance.location == "" and not Proxy.objects.filter(url=instance.url).exists():
        update_proxy_status(instance)
