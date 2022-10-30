import base64
import re

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models, IntegrityError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django_prometheus.models import ExportModelOperationsMixin

from proxylist.base64_decoder import decode_base64
from proxylist.proxy import update_proxy_status, get_proxy_location
from shadowmere import settings


def validate_sip002(value):
    if get_sip002(value) == "":
        raise ValidationError(
            "The value entered is not SIP002 compatible",
            params={"value": value},
        )


def validate_not_existing(value):
    if Proxy.objects.filter(url=get_sip002(value)):
        raise ValidationError(
            "This proxy was already imported",
            params={"value": value},
        )


def validate_proxy_can_connect(value):
    location = get_proxy_location(get_sip002(value))
    if location is None or location == "unknown":
        raise ValidationError(
            "Can't get the location for this address",
            params={"value": value},
        )


class Proxy(ExportModelOperationsMixin("proxy"), models.Model):
    url = models.CharField(
        max_length=1024,
        unique=True,
        validators=[
            validate_sip002,
            validate_not_existing,
            validate_proxy_can_connect,
        ],
        help_text="SIP002 compatible URL representing a key",
    )
    location = models.CharField(
        max_length=100,
        default="",
        help_text="Where is this proxy located geographically",
    )
    location_country_code = models.CharField(
        max_length=3, default="", help_text="2 letters country code (e.g.: DE)"
    )
    location_country = models.CharField(
        max_length=50, default="", help_text="Country hosting this proxy"
    )
    ip_address = models.CharField(
        max_length=100, default="", help_text="Proxy IP address"
    )
    port = models.IntegerField(default=0, help_text="Port used by this key")
    is_active = models.BooleanField(
        default=False,
        help_text=f"Whether or not this key worked in the past {settings.CHECK_INTERVAL_MINUTES} minutes",
    )
    last_checked = models.DateTimeField(
        auto_now=True, help_text="Last time this key was tested"
    )
    last_active = models.DateTimeField(
        blank=True,
        default=now,
        help_text="Last time this key responded positively to a test",
    )
    times_checked = models.IntegerField(
        default=0, help_text="How many times was this key tested so far"
    )
    times_check_succeeded = models.IntegerField(
        default=0, help_text="How many times this key responded positively to a test"
    )

    def __str__(self):
        return f"{self.location} ({self.url})"


def get_sip002(instance_url):
    try:
        url = instance_url
        if "#" in url:
            url = url.split("#")[0]
        if "=" in url:
            url = url.replace("=", "")
        if "@" not in url:
            url = url.replace("ss://", "")

            decoded_url = decode_base64(url.encode("ascii"))
            encoded_bits = (
                base64.b64encode(decoded_url.split(b"@")[0]).decode("ascii").rstrip("=")
            )
            url = f'ss://{encoded_bits}@{decoded_url.split(b"@")[1].decode("ascii")}'
    except IndexError:
        return ""

    return url


@receiver(post_save, sender=Proxy)
def update_url_and_location_after_save(sender, instance, created, **kwargs):
    url = get_sip002(instance.url)
    if url != instance.url:
        instance.url = url
        instance.save()
        return

    if instance.port == 0:
        server_and_port = instance.url.split("@")[1]
        instance.port = int(re.findall(r":(\d+)", server_and_port)[0])
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
