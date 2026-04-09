import inspect
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Iterator

import requests
from django.conf import settings
from django.core.cache import cache
from django.db.models import F, FloatField
from django.db.models.functions import Coalesce
from django.utils.timezone import now
from huey import crontab
from huey.contrib.djhuey import db_periodic_task
from requests.exceptions import SSLError, ConnectionError, ReadTimeout

from proxylist.base64_decoder import decode_base64
from proxylist.models import Proxy, Subscription, get_sip002
from proxylist.proxy import update_proxy_status, get_proxy_location

CONCURRENT_CHECKS = 300
SUBSCRIPTION_TIMEOUT_SECONDS = 60
LOW_QUALITY_THRESHOLD = 0.2

log = logging.getLogger("django")


def _current_task_name() -> str:
    frame = inspect.currentframe()
    caller = frame.f_back if frame else None
    return caller.f_code.co_name if caller else "unknown"


@db_periodic_task(crontab(minute="15", hour="10"))
def remove_low_quality_proxies_scheduled() -> None:
    remove_low_quality_proxies()


@db_periodic_task(crontab(minute="*/20"))
def update_status_scheduled() -> None:
    update_status()


@db_periodic_task(crontab(minute="0"))
def poll_subscriptions_scheduled() -> None:
    poll_subscriptions()


def remove_low_quality_proxies() -> None:
    log.info(
        "Removing low quality proxies",
        extra={"task": _current_task_name()},
    )
    start_time = now()
    deleted_count, _ = Proxy.objects.filter(
        is_active=False,
        times_checked__gt=1,
        times_check_succeeded__lt=Coalesce(
            F("times_checked") * LOW_QUALITY_THRESHOLD, 0, output_field=FloatField()
        ),
    ).delete()
    log.info(
        f"Removed {deleted_count} low quality proxies",
        extra={
            "task": _current_task_name(),
            "removed": deleted_count,
            "start_time": start_time,
            "finish_time": now(),
        },
    )


def update_status():
    log.info(
        "Updating proxies status", extra={"task": _current_task_name()}
    )
    start_time = now()

    try:
        req = requests.get("https://clients3.google.com/generate_204")
    except (SSLError, ConnectionError, ReadTimeout):
        log.error(
            "The Shadowmere host is having connection issues. Skipping test cycle."
        )
        return

    log.info("Using ShadowTest URLs", extra={"url": settings.SHADOWTEST_SERVERS})

    if req.status_code == 204:
        proxies = list(Proxy.objects.all())
        with ThreadPoolExecutor(max_workers=CONCURRENT_CHECKS) as executor:
            executor.map(update_proxy_status, proxies)
            executor.shutdown(wait=True)

        log.info(
            "Proxies statuses checked. Saving new status now.",
            extra={"task": _current_task_name()},
        )

        update_fields = [
            "is_active",
            "ip_address",
            "last_active",
            "location",
            "location_country_code",
            "location_country",
            "times_checked",
            "times_check_succeeded",
            "last_checked",
        ]
        saved_proxies = 0
        deleted_proxies = 0
        proxies_to_update = []

        for proxy in proxies:
            try:
                # Validate uniqueness before batching
                proxies_to_update.append(proxy)
                saved_proxies += 1
            except Exception:
                deleted_proxies += 1

        if proxies_to_update:
            Proxy.objects.bulk_update(proxies_to_update, update_fields, batch_size=500)
            cache.clear()

        log.info(
            "Update completed",
            extra={
                "task": _current_task_name(),
                "saved": saved_proxies,
                "deleted": deleted_proxies,
                "start_time": start_time,
                "finish_time": now(),
            },
        )
    else:
        log.error(
            "The Shadowmere host is having connection issues. Skipping test cycle.",
            extra={"task": _current_task_name()},
        )


def decode_line(line: str | bytes) -> list[str] | None:
    try:
        if isinstance(line, str):
            line = line.encode("utf-8")
        decoded = decode_base64(line)
        if decoded is None:
            log.warning(
                "Base64 decoding returned None",
                extra={
                    "task": _current_task_name(),
                    "line": line[:200],
                },
            )
            return None
        return decoded.decode("utf-8", errors="replace").split("\n")
    except Exception as error:
        log.error(
            "Failed decoding line",
            extra={
                "task": _current_task_name(),
                "line": line[:200] if line else "",
                "error": error,
            },
        )
        return None


def poll_subscriptions() -> None:
    log.info(
        "Started polling subscriptions",
        extra={"task": _current_task_name()},
    )
    start_time = now()
    all_urls = set(Proxy.objects.values_list("url", flat=True))

    # Phase 1: Fetch all subscriptions and aggregate unique candidate URLs.
    # Using a set means duplicate addresses across subscriptions are collapsed
    # automatically — each address will be connectivity-tested at most once.
    candidate_urls: set[str] = set()
    subscriptions = Subscription.objects.filter(enabled=True)
    for subscription in subscriptions:
        log.info(
            "Fetching subscription",
            extra={
                "task": _current_task_name(),
                "subscription": subscription.url,
            },
        )
        try:
            r = requests.get(subscription.url, timeout=SUBSCRIPTION_TIMEOUT_SECONDS)
            if r.status_code != 200:
                error_message = f"We are facing issues getting this subscription {subscription.url} ({r.status_code} {r.text})"
                log.warning(
                    error_message,
                    extra={
                        "task": _current_task_name(),
                        "subscription": subscription.url,
                        "status_code": r.status_code,
                        "text": r.text,
                    },
                )
                subscription.alive = False
                subscription.error_message = error_message[:10000]
                subscription.save()
                continue
            if subscription.kind == Subscription.SubscriptionKind.PLAIN:
                lines = [line.decode("utf-8") for line in r.iter_lines()]
            elif subscription.kind == Subscription.SubscriptionKind.BASE64:
                joined = b"".join(r.iter_lines())
                lines = decode_line(line=joined) or []
            else:
                lines = []
            for line in lines:
                url = extract_sip002_url(line)
                if url:
                    candidate_urls.add(url)
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
            log.error(
                "Failed to get subscription",
                extra={
                    "error": f"{e}",
                    "task": _current_task_name(),
                    "subscription": subscription.url,
                },
            )
            subscription.error_message = f"{e}"
            subscription.alive = False
        except AttributeError as e:
            log.warning(
                "Error decoding subscription",
                extra={
                    "task": _current_task_name(),
                    "error": f"{e}",
                    "subscription": subscription.url,
                },
            )
            subscription.error_message = f"{e}"
            subscription.alive = False

        subscription.save()

    # Remove addresses already in the database — no need to re-test them.
    candidate_urls -= all_urls

    # Phase 2: Test connectivity for deduplicated, new-only URLs in parallel.
    log.info(
        "Testing unique new addresses",
        extra={"task": _current_task_name(), "count": len(candidate_urls)},
    )
    with ThreadPoolExecutor(max_workers=CONCURRENT_CHECKS) as executor:
        proxy_results = list(executor.map(test_and_create_proxy, candidate_urls))

    saved_proxies, found_proxies = save_proxies(proxies_lists=[proxy_results])

    log.info(
        "Finished polling subscriptions",
        extra={
            "task": _current_task_name(),
            "found": found_proxies,
            "saved": saved_proxies,
            "start_time": start_time,
            "finish_time": now(),
        },
    )


def save_proxies(proxies_lists):
    log.info(
        "Saving proxies",
        extra={"task": _current_task_name()},
    )
    saved_proxies = 0
    found_proxies = 0
    for proxy_list in proxies_lists:
        for proxy in proxy_list:
            if proxy is not None:
                found_proxies += 1
                log.info(
                    f"saving {proxy}",
                    extra={"task": _current_task_name()},
                )
                try:
                    proxy.save()
                    saved_proxies += 1
                except Exception as e:
                    log.warning(
                        "Failed to save proxy",
                        extra={
                            "task": _current_task_name(),
                            "proxy": proxy,
                            "error": f"{e}",
                        },
                    )
    return saved_proxies, found_proxies


NON_SS_SCHEMES = (
    "vmess://",
    "vless://",
    "trojan://",
    "hysteria://",
    "hy2://",
    "tuic://",
    "http://",
    "https://",
)


def extract_sip002_url(line: str) -> str | None:
    """Normalize and validate a SIP002 URL format without testing connectivity.

    Returns the normalized URL string if the line is a valid ss:// address,
    else None.  Does not check whether the address already exists in the DB.
    """
    line = str(line).strip()
    if not line.startswith("ss://"):
        return None
    if line.startswith(NON_SS_SCHEMES):
        return None
    try:
        url = get_sip002(line)
    except UnicodeDecodeError:
        return None
    return url or None


def test_and_create_proxy(url: str) -> Proxy | None:
    """Test connectivity for a SIP002 URL and return a Proxy object if reachable."""
    location = get_proxy_location(url)
    if location is None or location == "unknown":
        return None
    return Proxy(url=url)


def process_line(line, all_urls):
    url = extract_sip002_url(line)
    if url is None or url in all_urls:
        return None
    return test_and_create_proxy(url)


def flatten(something) -> Iterator[str]:
    if isinstance(something, (list, tuple, set, range)):
        for sub in something:
            yield from flatten(something=sub)
    else:
        yield something
