from django.db import models
from django.utils.timezone import now
from django_prometheus.models import ExportModelOperationsMixin
from utils.validators import proxy_validator


class Proxy(ExportModelOperationsMixin("proxy"), models.Model):
    url = models.CharField(
        max_length=1024,
        unique=True,
        validators=[
            proxy_validator,
        ],
    )
    location = models.CharField(max_length=100, blank=True, null=True)
    location_country_code = models.CharField(max_length=3, blank=True, null=True, db_index=True)
    location_country = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    ip_address = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    port = models.IntegerField(default=0, db_index=True)
    is_active = models.BooleanField(default=False, db_index=True)
    last_checked = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(blank=True, default=now)
    times_checked = models.IntegerField(default=0)
    times_check_succeeded = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.location} ({self.url})"


class Subscription(models.Model):
    class SubscriptionKind(models.TextChoices):
        PLAIN = "PLAIN", "plain"
        BASE64 = "BASE64", "base64"

    url = models.URLField(null=False, unique=True)
    kind = models.CharField(choices=SubscriptionKind.choices, default=SubscriptionKind.PLAIN, max_length=10)
    alive = models.BooleanField(default=True)
    alive_timestamp = models.DateTimeField(default=now)
    enabled = models.BooleanField(default=True)
    error_message = models.CharField(max_length=10000, default="")

    def __str__(self):
        return f"{self.url} - {self.kind}"


class TaskLog(models.Model):
    name = models.CharField(max_length=100)
    details = models.CharField(max_length=1000, default="")
    start_time = models.DateTimeField(auto_now=False)
    finish_time = models.DateTimeField(auto_now=False)

    def __str__(self):
        return f"{self.name} - {self.finish_time}"
