from concurrent.futures import ThreadPoolExecutor

import requests
from django.db import IntegrityError

from proxylist.models import Proxy, Subscription, get_sip002
from proxylist.proxy import update_proxy_status, get_proxy_location
from shadowmere.celery import app

CONCURRENT_CHECKS = 120


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
    print("Started polling subscriptions")
    for subscription in Subscription.objects.all():
        print(f"Testing subscription {subscription.url}")
        r = requests.get(subscription.url)
        if r.status_code != 200:
            print(f"We are facing issues getting this subscription {subscription.url}")
            continue
        if subscription.kind == Subscription.SubscriptionKind.PLAIN:
            for line in r.iter_lines():
                if line:
                    try:
                        line = line.decode("utf-8")
                        if not str(line).startswith("ss://"):
                            continue
                        url = get_sip002(line)
                        if url:
                            print(f"Testing {url}")
                            if Proxy.objects.filter(url=get_sip002(url)):
                                continue
                            location = get_proxy_location(url)
                            if location is None or location == "unknown":
                                continue
                            proxy = Proxy(url=url)
                            proxy.save()
                    except UnicodeDecodeError:
                        # False positives fall in here
                        pass

    print("Finished polling subscriptions")
