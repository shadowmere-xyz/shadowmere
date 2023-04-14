import logging

import requests
from django.utils.timezone import now

from shadowmere import settings


def get_proxy_location(proxy_url):
    r = requests.post(settings.SHADOWTEST_URL, data={"address": proxy_url})

    if r.status_code != 200:
        return None

    output = r.json()
    if "YourFuckingLocation" not in output:
        return None

    return output


def get_location_country_name(country_code: str) -> str:
    try:
        r = requests.get(f"https://restcountries.akiel.dev/v3.1/alpha/{country_code.lower()}")
        if r.status_code != 200:
            return ""

        return r.json()[0].get("name").get("common")
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Failed to connect to restcountries {e}")
        return "Unknown"


def update_proxy_status(proxy):
    ip_information = get_proxy_location(proxy_url=proxy.url)

    if ip_information:
        proxy.is_active = True
        proxy.ip_address = ip_information.get("YourFuckingIPAddress")
        proxy.last_active = now()
        proxy.times_check_succeeded = proxy.times_check_succeeded + 1
        if proxy.location != ip_information.get("YourFuckingLocation") or proxy.location_country == "":
            proxy.location = ip_information.get("YourFuckingLocation")
            proxy.location_country_code = ip_information.get("YourFuckingCountryCode")
            proxy.location_country = get_location_country_name(
                country_code=ip_information.get("YourFuckingCountryCode")
            )
    else:
        proxy.is_active = False
        proxy.location = "unknown"

    proxy.times_checked = proxy.times_checked + 1
