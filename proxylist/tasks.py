from concurrent.futures import ThreadPoolExecutor

from proxylist.models import Proxy
from proxylist.proxy import update_proxy_status
from shadowmere.celery import app

CONCURRENT_CHECKS = 10


@app.task(bind=True)
def update_status(self):
    print("Updating proxies status")

    with ThreadPoolExecutor(max_workers=CONCURRENT_CHECKS) as executor:
        executor.map(update_proxy_status, Proxy.objects.all())

    print("Proxy status checked")
