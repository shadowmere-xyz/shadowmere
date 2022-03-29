import socket
from contextlib import closing

import requests
from django.utils.timezone import now

from shadowmere import settings


def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def get_proxy_location(proxy_url):
    r = requests.post(settings.SHADOWTEST_URL, data={'address': proxy_url})
    output = r.json()
    if r.status_code != 200 or "YourFuckingLocation" not in output:
        return None
    return f'{output.get("YourFuckingIPAddress")} @ {output.get("YourFuckingLocation")}'


def update_proxy_status(proxy):
    location = get_proxy_location(proxy_url=proxy.url)
    if location:
        proxy.is_active = True
        proxy.location = location
        proxy.last_active = now()
    else:
        proxy.is_active = False
        proxy.location = "unknown"
    proxy.save()
