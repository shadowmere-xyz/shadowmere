from threading import Thread

from proxylist.models import Proxy
from proxylist.proxy import update_proxy_status
from shadowmere.celery import app

CONCURRENT_CHECKS = 10


@app.task(bind=True)
def update_status(self):
    print("Updating proxies status")
    for proxy in Proxy.objects.all():
        print(f"\t>>>{proxy.url}")
        Thread(target=update_proxy_status, args=(proxy,)).start()
    print("Proxy status checked")
