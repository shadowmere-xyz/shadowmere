from concurrent.futures import ThreadPoolExecutor

import requests
from django.db import IntegrityError

from proxylist.models import Proxy
from proxylist.proxy import update_proxy_status
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
