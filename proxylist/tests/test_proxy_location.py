from unittest.mock import Mock, patch

from django.core.cache import caches
from django.test import TestCase
from requests.exceptions import InvalidJSONError

from proxylist import proxy as proxy_module
from proxylist.proxy import NO_LOCATION, get_proxy_location

LOCATION_PAYLOAD = {"Location": "Amsterdam", "CountryCode": "NL", "IPAddress": "1.2.3.4"}


def _response(status_code, json_value=None, json_error=False):
    resp = Mock()
    resp.status_code = status_code
    if json_error:
        resp.json.side_effect = InvalidJSONError()
    else:
        resp.json.return_value = json_value
    return resp


class GetProxyLocationCacheTest(TestCase):
    def setUp(self):
        caches["proxy_location"].clear()

    @patch("proxylist.proxy.requests.post")
    def test_positive_result_is_cached_and_reused(self, mock_post):
        mock_post.return_value = _response(200, LOCATION_PAYLOAD)

        first = get_proxy_location("ss://proxy@1.2.3.4:8388")
        second = get_proxy_location("ss://proxy@1.2.3.4:8388")

        self.assertEqual(first, LOCATION_PAYLOAD)
        self.assertEqual(second, LOCATION_PAYLOAD)
        mock_post.assert_called_once()

    @patch("proxylist.proxy.requests.post")
    def test_missing_location_is_cached_as_negative(self, mock_post):
        mock_post.return_value = _response(200, {"IPAddress": "1.2.3.4"})

        self.assertIsNone(get_proxy_location("ss://proxy@1.2.3.4:8388"))
        self.assertIsNone(get_proxy_location("ss://proxy@1.2.3.4:8388"))
        mock_post.assert_called_once()

    @patch("proxylist.proxy.requests.post")
    def test_non_200_is_cached_as_negative(self, mock_post):
        mock_post.return_value = _response(404)

        self.assertIsNone(get_proxy_location("ss://proxy@1.2.3.4:8388"))
        self.assertIsNone(get_proxy_location("ss://proxy@1.2.3.4:8388"))
        mock_post.assert_called_once()

    @patch("proxylist.proxy.requests.post")
    def test_invalid_json_is_cached_as_negative(self, mock_post):
        mock_post.return_value = _response(200, json_error=True)

        self.assertIsNone(get_proxy_location("ss://proxy@1.2.3.4:8388"))
        self.assertIsNone(get_proxy_location("ss://proxy@1.2.3.4:8388"))
        mock_post.assert_called_once()

    @patch("proxylist.proxy.requests.post")
    def test_negative_sentinel_is_stored(self, mock_post):
        import hashlib

        proxy_url = "ss://proxy@1.2.3.4:8388"
        mock_post.return_value = _response(404)
        get_proxy_location(proxy_url)

        digest = hashlib.sha256(proxy_url.encode("utf-8", errors="ignore")).hexdigest()
        cache_key = f"proxy_location:{digest}"
        self.assertEqual(caches["proxy_location"].get(cache_key), NO_LOCATION)


class LocationCacheIsolationTest(TestCase):
    """Clearing the default (page) cache must not wipe proxy locations."""

    def setUp(self):
        caches["default"].clear()
        caches["proxy_location"].clear()

    def test_default_clear_keeps_proxy_location(self):
        caches["default"].set("page-response", "cached")
        caches["proxy_location"].set("proxy_location:abc", LOCATION_PAYLOAD)

        caches["default"].clear()

        self.assertIsNone(caches["default"].get("page-response"))
        self.assertEqual(
            caches["proxy_location"].get("proxy_location:abc"), LOCATION_PAYLOAD
        )

    def test_location_cache_is_a_separate_backend(self):
        self.assertIsNot(caches["default"], proxy_module.location_cache)
        self.assertIs(caches["proxy_location"], proxy_module.location_cache)
