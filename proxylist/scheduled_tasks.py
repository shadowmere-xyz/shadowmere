from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from proxylist.tasks import (
    remove_low_quality_proxies,
    update_status,
    poll_subscriptions,
)


@db_periodic_task(crontab(minute="15", hour="10"))
def remove_low_quality_proxies_scheduled():
    remove_low_quality_proxies()


@db_periodic_task(crontab(minute="*/20"))
def update_status_scheduled():
    update_status()


@db_periodic_task(crontab(minute="0"))
def poll_subscriptions_scheduled():
    poll_subscriptions()
