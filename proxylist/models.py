import base64
import logging
import re

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.timezone import now
from django_prometheus.models import ExportModelOperationsMixin

from proxylist.base64_decoder import decode_base64
from proxylist.proxy import update_proxy_status, get_proxy_location

log = logging.getLogger("django")


def validate_sip002(value) -> None:
    if get_sip002(instance_url=value) == "":
        raise ValidationError(
            "The value entered is not SIP002 compatible",
            params={"value": value},
        )


def validate_not_existing(value) -> None:
    if Proxy.objects.filter(url=get_sip002(instance_url=value)):
        raise ValidationError(
            "This proxy was already imported",
            params={"value": value},
        )


def validate_proxy_can_connect(value) -> None:
    location = get_proxy_location(get_sip002(instance_url=value))
    if location is None or location == "unknown":
        raise ValidationError(
            "Can't get the location for this address",
            params={"value": value},
        )


def validete_proxy_is_not_blacklisted(value) -> None:
    sip002 = get_sip002(instance_url=value)
    if "@" in sip002:
        server_and_port = sip002.split("@")[1]
        server = re.findall(r"^(.*):\d+$", server_and_port)
        if server and BlackListHost.objects.filter(host=server[0]).exists():
            raise ValidationError(
                "This host is blacklisted",
                params={"value": value},
            )


def proxy_validator(value) -> None:
    validate_sip002(value=value)
    validete_proxy_is_not_blacklisted(value=value)
    validate_not_existing(value=value)
    validate_proxy_can_connect(value=value)


class Proxy(ExportModelOperationsMixin("proxy"), models.Model):
    url = models.CharField(
        max_length=1024,
        unique=True,
        validators=[
            proxy_validator,
        ],
    )
    location = models.CharField(max_length=100, default="")
    location_country_code = models.CharField(max_length=3, default="", db_index=True)
    location_country = models.CharField(max_length=50, default="")
    ip_address = models.CharField(max_length=100, default="")
    port = models.IntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=False, db_index=True)
    last_checked = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(blank=True, default=now)
    times_checked = models.IntegerField(default=0)
    times_check_succeeded = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["is_active", "location_country_code"]),
            models.Index(fields=["is_active", "port"]),
            models.Index(fields=["is_active", "last_active"]),
        ]

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
            decoded_url = decode_base64(url.encode("ascii", errors="ignore"))
            if decoded_url:
                encoded_bits = (
                    base64.b64encode(decoded_url.split(b"@")[0])
                    .decode("ascii")
                    .rstrip("=")
                )
                url = (
                    f'ss://{encoded_bits}@{decoded_url.split(b"@")[1].decode("ascii")}'
                )
            else:
                return ""
        if "?" in url:
            url = url.split("?")[0]
        url = url.rstrip("/")
    except (IndexError, UnicodeEncodeError):
        log.warning(
            "Unable to decode SIP002",
            extra={
                "url": instance_url,
            },
        )
        return ""

    return url


@receiver(pre_save, sender=Proxy)
def normalize_proxy_before_save(sender, instance, **kwargs):
    # Normalize URL, derive the port and fetch the location before the row is
    # written, so a single save persists everything instead of triggering a
    # chain of recursive re-saves.
    url = get_sip002(instance_url=instance.url)
    if url and url != instance.url:
        instance.url = url

    if instance.port == 0 and "@" in instance.url:
        server_and_port = instance.url.split("@")[1]
        ports = re.findall(r":(\d+)", server_and_port)
        if ports:
            instance.port = int(ports[-1])

    if instance.location == "":
        update_proxy_status(instance)


@receiver(post_save, sender=Proxy)
def clear_cache(sender, instance, **kwargs) -> None:
    cache.clear()


class Subscription(models.Model):
    class SubscriptionKind(models.TextChoices):
        PLAIN = "PLAIN", "plain"
        BASE64 = "BASE64", "base64"

    url = models.URLField(null=False, unique=True)
    kind = models.CharField(
        choices=SubscriptionKind.choices, default=SubscriptionKind.PLAIN, max_length=10
    )
    alive = models.BooleanField(default=True)
    alive_timestamp = models.DateTimeField(default=now)
    enabled = models.BooleanField(default=True)
    error_message = models.CharField(max_length=10000, default="")

    def __str__(self):
        return f"{self.url} - {self.kind}"


class BlackListHost(models.Model):
    host = models.CharField(max_length=1024, unique=True)

    def __str__(self):
        return self.host
