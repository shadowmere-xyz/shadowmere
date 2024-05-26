import re

import flag
import requests
from django.utils.timezone import now
from requests.exceptions import InvalidJSONError

from proxylist.base64_decoder import decode_base64
from shadowmere import settings


def get_flag_or_empty(country_code):
    if country_code != "":
        return flag.flag(country_code)
    return ""


def get_proxy_config(proxy):
    method_password = decode_base64(
        proxy.url.split("@")[0].replace("ss://", "").encode("ascii")
    )
    server_and_port = proxy.url.split("@")[1]
    config = {
        "server": re.findall(r"^(.*?):\d+", server_and_port)[0],
        "server_port": int(re.findall(r":(\d+)", server_and_port)[0]),
        "password": method_password.decode("ascii").split(":")[1],
        "method": method_password.decode("ascii").split(":")[0],
        "plugin": "",
        "plugin_opts": None,
        "remarks": f"{get_flag_or_empty(proxy.location_country_code)} {proxy.location}",
    }

    return config


def get_proxy_location(proxy_url):
    r = requests.post(settings.SHADOWTEST_URL, data={"address": proxy_url})

    if r.status_code != 200:
        return None
    try:
        output = r.json()
        if "YourFuckingLocation" not in output:
            return None
    except InvalidJSONError:
        return None

    return output


def update_proxy_status(proxy):
    ip_information = get_proxy_location(proxy_url=proxy.url)

    if ip_information:
        proxy.is_active = True
        proxy.ip_address = ip_information.get("YourFuckingIPAddress")
        proxy.last_active = now()
        proxy.times_check_succeeded = proxy.times_check_succeeded + 1
        if (
            proxy.location != ip_information.get("YourFuckingLocation")
            or proxy.location_country == ""
        ):
            proxy.location = ip_information.get("YourFuckingLocation")
            proxy.location_country_code = ip_information.get("YourFuckingCountryCode")
            proxy.location_country = ip_information.get("YourFuckingCountry")
    else:
        proxy.is_active = False
        proxy.location = "unknown"
        proxy.location_country = ""
        proxy.location_country_code = ""

    proxy.times_checked = proxy.times_checked + 1
