import hashlib
import logging
import time
from itertools import cycle

import requests
from django.core.cache import cache
from django.utils.timezone import now
from requests import ReadTimeout
from requests.exceptions import InvalidJSONError, SSLError
from urllib3.exceptions import MaxRetryError

from shadowmere.settings import CACHE_LOCATION_SECONDS, SHADOWTEST_SERVERS

log = logging.getLogger("django")

shadowtest_iterator = cycle(SHADOWTEST_SERVERS)


class ShadowtestError(Exception):
    pass


def get_proxy_location(proxy_url):
    # Return the cached result if it exists
    # This should make t easier for the testing mechanism by avoiding double testing
    cache_key = f"proxy_location:{hashlib.sha256(proxy_url.encode('utf-8', errors='ignore')).hexdigest()}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        log.info(
            "Using cached location",
            extra={"source": "get_proxy_location", "address": proxy_url},
        )
        return cached_result

    retries = 5
    delay = 1

    for attempt in range(retries):
        errored = False
        r = None
        try:
            shadowtest_url = next(shadowtest_iterator)
            r = requests.post(shadowtest_url, data={"address": proxy_url})
        except (SSLError, ReadTimeout, MaxRetryError) as e:
            log.error(
                f"Error connecting to Shadowtest: {e}",
                extra={"source": "get_proxy_location", "address": proxy_url},
            )
            errored = True

        if errored or r.status_code == 500:
            log.warning(
                f"Shadowtest error encountered. Retry {attempt + 1}/{retries} after {delay} seconds.",
                extra={"source": "get_proxy_location", "address": proxy_url},
            )
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            else:
                log.error(
                    "Max retries reached. Giving up on getting proxy location.",
                    extra={"source": "get_proxy_location", "address": proxy_url},
                )
                raise ShadowtestError()

        if r.status_code != 200:
            return None
        try:
            output = r.json()
            if "YourFuckingLocation" not in output:
                return None
        except InvalidJSONError:
            return None

        cache.set(cache_key, output, CACHE_LOCATION_SECONDS)
        return output


def update_proxy_status(proxy) -> None:
    try:
        ip_information = get_proxy_location(proxy_url=proxy.url)
    except ShadowtestError:
        log.error(f"Shadowtest is experiencing issues. Skipping updating {proxy.id}")
        return

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
