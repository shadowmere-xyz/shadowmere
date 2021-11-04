from multiprocessing.pool import ThreadPool

from proxylist.models import Proxy
from proxylist.proxy import update_proxy_status
from shadowmere.celery import app

CONCURRENT_CHECKS = 10


@app.task(bind=True)
def update_status(self):
    print("Updating proxies status")
    pool = ThreadPool(processes=int(CONCURRENT_CHECKS))

    for proxy in Proxy.objects.all():
        print(f"\t>>>{proxy.url}")
        pool.apply_async(update_proxy_status, [proxy, ])

    pool.terminate()
    print("Proxy status checked")
