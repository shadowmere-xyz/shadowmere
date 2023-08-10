import logging
from concurrent.futures import ThreadPoolExecutor

import requests
from django.db import IntegrityError
from requests.exceptions import SSLError

from proxylist.base64_decoder import decode_base64
from proxylist.models import Proxy, Subscription, get_sip002
from proxylist.proxy import update_proxy_status, get_proxy_location
from shadowmere.celery import app

CONCURRENT_CHECKS = 500


@app.task(bind=True)
def update_status(self):
    print("Updating proxies status")

    req = requests.get("https://clients3.google.com/generate_204")
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
    else:
        print("This host is having connection issues. Skipping test cycle.")


@app.task(bind=True)
def poll_subscriptions(self):
    logging.info("Started polling subscriptions")

    all_urls = [proxy.url for proxy in Proxy.objects.all()]

    proxies_lists = []
    with ThreadPoolExecutor(max_workers=CONCURRENT_CHECKS) as executor:
        for subscription in Subscription.objects.filter(enabled=True):
            logging.info(f"Testing subscription {subscription.url}")
            try:
                r = requests.get(subscription.url)
                if r.status_code != 200:
                    logging.error(
                        f"We are facing issues getting this subscription {subscription.url}"
                    )
                    subscription.alive = False
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
                    decoded = [
                        decode_base64(line).decode("utf-8").split("\n")
                        for line in r.iter_lines()
                    ]
                    flatten_decoded = list(flatten(decoded))
                    proxies_lists.append(
                        executor.map(
                            process_line,
                            flatten_decoded,
                            [all_urls] * len(flatten_decoded),
                        )
                    )
                if subscription.alive is False:
                    subscription.alive = True
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.SSLError,
            ) as e:
                logging.warning(f"Failed to get subscription {subscription.url}, {e}")
                subscription.alive = False
            except AttributeError as e:
                logging.warning(f"Error decoding subscription {subscription.url}, {e}")
                subscription.alive = False

            subscription.save()

    save_proxies(proxies_lists)

    executor.shutdown(wait=True)
    print("Finished polling subscriptions")


def save_proxies(proxies_lists):
    logging.info("Saving proxies")
    for proxy_list in proxies_lists:
        for proxy in proxy_list:
            if proxy is not None:
                logging.info(f"saving {proxy}")
                try:
                    proxy.save()
                except Exception as e:
                    logging.warning(f"Failed to save proxy {proxy}, {e}")


def process_line(line, all_urls):
    if not str(line).startswith("ss://"):
        return None
    try:
        url = get_sip002(line)
    except UnicodeDecodeError:
        # False positives fall in here
        return None
    if url and url not in all_urls:
        print(f"Testing {url}")
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
