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

    if r.status_code != 200:
        return None

    output = r.json()
    if "YourFuckingLocation" not in output:
        return None

    return output


def update_proxy_status(proxy):
    ip_information = get_proxy_location(proxy_url=proxy.url)

    if ip_information:
        proxy.is_active = True
        proxy.location = ip_information.get('YourFuckingLocation')
        proxy.location_country_code = ip_information.get('YourFuckingCountryCode')
        proxy.ip_address = ip_information.get('YourFuckingIPAddress')
        proxy.last_active = now()
        proxy.times_check_succeeded = proxy.times_check_succeeded + 1
    else:
        proxy.is_active = False
        proxy.location = "unknown"

    proxy.times_checked = proxy.times_checked + 1
    proxy.save()
