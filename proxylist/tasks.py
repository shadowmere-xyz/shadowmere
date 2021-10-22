from proxylist.models import Proxy
from proxylist.proxy import update_proxy_status
from shadowmere.celery import app


@app.task(bind=True)
def update_status(self):
    print("Updating proxies status")
    for proxy in Proxy.objects.all():
        print(f"\t>>>{proxy.url}")
        update_proxy_status(proxy)
    print("Proxy status checked")
