import logging
from concurrent.futures import ThreadPoolExecutor

import requests
from django.db import IntegrityError
from django.db.models import F, FloatField
from django.db.models.functions import Coalesce
from django.utils.timezone import now
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
from requests.exceptions import SSLError, ConnectionError, ReadTimeout

from proxylist.base64_decoder import decode_base64
from proxylist.models import Proxy, Subscription, get_sip002, TaskLog
from proxylist.proxy import update_proxy_status, get_proxy_location

CONCURRENT_CHECKS = 200
SUBSCRIPTION_TIMEOUT_SECONDS = 60
LOW_QUALITY_THRESHOLD = 0.2


@db_periodic_task(crontab(minute="15", hour="10"))
def remove_low_quality_proxies_scheduled():
    remove_low_quality_proxies()


@db_periodic_task(crontab(minute="*/20"))
def update_status_scheduled():
    update_status()


@db_periodic_task(crontab(minute="0"))
def poll_subscriptions_scheduled():
    poll_subscriptions()


def remove_low_quality_proxies():
    print("Removing low quality proxies")
    start_time = now()
    deleted_count, _ = Proxy.objects.filter(
        is_active=False,
        times_checked__gt=1,
        times_check_succeeded__lt=Coalesce(
            F("times_checked") * LOW_QUALITY_THRESHOLD, 0, output_field=FloatField()
        ),
    ).delete()
    TaskLog.objects.create(
        name="remove_low_quality_proxies",
        details=f"Removed {deleted_count} low quality proxies",
        start_time=start_time,
        finish_time=now(),
    )
    print(f"Removed {deleted_count} low quality proxies")


def update_status():
    print("Updating proxies status")
    start_time = now()

    try:
        req = requests.get("https://clients3.google.com/generate_204")
    except (SSLError, ConnectionError, ReadTimeout):
        print("The Shadowmere host is having connection issues. Skipping test cycle.")
        return

    if req.status_code == 204:
        proxies = Proxy.objects.all()
        with ThreadPoolExecutor(max_workers=CONCURRENT_CHECKS) as executor:
            executor.map(update_proxy_status, proxies)
            executor.shutdown(wait=True)

        print("Proxy status checked")

        print("Saving new status")
        for proxy in proxies:
            try:
                proxy.save()
            except IntegrityError:
                # This means the proxy is either a duplicate or no longer valid
                proxy.delete()

        print("Update completed")
        TaskLog.objects.create(
            name="update_status", start_time=start_time, finish_time=now()
        )
    else:
        print("The Shadowmere host is having connection issues. Skipping test cycle.")


def decode_line(line):
    try:
        return decode_base64(line).decode("utf-8").split("\n")
    except UnicodeDecodeError:
        logging.warning(f"Failed decoding line: {line}")


def poll_subscriptions():
    logging.info("Started polling subscriptions")
    start_time = now()
    all_urls = [proxy.url for proxy in Proxy.objects.all()]

    proxies_lists = []
    with ThreadPoolExecutor(max_workers=CONCURRENT_CHECKS) as executor:
        subscriptions = Subscription.objects.filter(enabled=True)
        for subscription in subscriptions:
            logging.info(f"Testing subscription {subscription.url}")
            try:
                r = requests.get(subscription.url, timeout=SUBSCRIPTION_TIMEOUT_SECONDS)
                if r.status_code != 200:
                    error_message = f"We are facing issues getting this subscription {subscription.url} ({r.status_code} {r.text})"
                    logging.warning(error_message)
                    subscription.alive = False
                    subscription.error_message = error_message[:10000]
                    subscription.save()
                    continue
                if subscription.kind == Subscription.SubscriptionKind.PLAIN:
                    decoded_lines = [line.decode("utf-8") for line in r.iter_lines()]
                    proxies_lists.append(
                        executor.map(
                            process_line, decoded_lines, [all_urls] * len(decoded_lines)
                        )
                    )
                elif subscription.kind == Subscription.SubscriptionKind.BASE64:
                    decoded = [decode_line(line) for line in r.iter_lines()]
                    flatten_decoded = list(flatten(decoded))
                    proxies_lists.append(
                        executor.map(
                            process_line,
                            flatten_decoded,
                            [all_urls] * len(flatten_decoded),
                        )
                    )
                subscription.alive_timestamp = now()
                if subscription.alive is False:
                    subscription.alive = True
                if subscription.error_message != "":
                    subscription.error_message = ""
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.SSLError,
                requests.exceptions.ReadTimeout,
            ) as e:
                logging.warning(f"Failed to get subscription {subscription.url}, {e}")
                subscription.error_message = f"{e}"
                subscription.alive = False
            except AttributeError as e:
                logging.warning(f"Error decoding subscription {subscription.url}, {e}")
                subscription.error_message = f"{e}"
                subscription.alive = False

            subscription.save()

    saved_proxies, found_proxies = save_proxies(proxies_lists)

    executor.shutdown(wait=True)
    TaskLog.objects.create(
        name="poll_subscriptions",
        details=f"Polled {len(subscriptions)} subscriptions and found {found_proxies} proxies from which we managed to save {saved_proxies}.",
        start_time=start_time,
        finish_time=now(),
    )
    print("Finished polling subscriptions")


def save_proxies(proxies_lists):
    logging.info("Saving proxies")
    saved_proxies = 0
    found_proxies = 0
    for proxy_list in proxies_lists:
        for proxy in proxy_list:
            if proxy is not None:
                found_proxies += 1
                logging.info(f"saving {proxy}")
                try:
                    proxy.save()
                    saved_proxies += 1
                except Exception as e:
                    logging.warning(f"Failed to save proxy {proxy}, {e}")
    return saved_proxies, found_proxies


def process_line(line, all_urls):
    if not str(line).startswith("ss://"):
        return None
    try:
        url = get_sip002(line)
    except UnicodeDecodeError:
        # False positives fall in here
        return None
    if url and url not in all_urls:
        # print(f"Testing {url}")
        location = get_proxy_location(url)
        if location is None or location == "unknown":
            return None
        proxy = Proxy(url=url)
        return proxy


def flatten(something):
    if isinstance(something, (list, tuple, set, range)):
        for sub in something:
            yield from flatten(sub)
    else:
        yield something
