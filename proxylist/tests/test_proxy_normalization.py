from unittest.mock import patch

from django.test import TestCase

from proxylist.models import Proxy, normalize_proxy_before_save


class NormalizeProxyBeforeSaveTest(TestCase):
    def test_normalizes_url_derives_port_and_fetches_location(self):
        proxy = Proxy(
            url="ss://YWVzLTI1Ni1nY206cGFzcw==@10.0.0.9:8388#tag",
            port=0,
            location="",
        )

        with patch("proxylist.models.update_proxy_status") as mock_update:
            normalize_proxy_before_save(sender=Proxy, instance=proxy)

        self.assertEqual(proxy.url, "ss://YWVzLTI1Ni1nY206cGFzcw@10.0.0.9:8388")
        self.assertEqual(proxy.port, 8388)
        mock_update.assert_called_once_with(proxy)

    def test_does_not_fetch_location_when_already_set(self):
        proxy = Proxy(url="ss://abc@1.2.3.4:8388", port=8388, location="Somewhere")

        with patch("proxylist.models.update_proxy_status") as mock_update:
            normalize_proxy_before_save(sender=Proxy, instance=proxy)

        mock_update.assert_not_called()

    def test_keeps_url_when_get_sip002_returns_empty(self):
        proxy = Proxy(url="ss://abc@1.2.3.4:8388", port=8388, location="X")

        with patch("proxylist.models.get_sip002", return_value=""):
            with patch("proxylist.models.update_proxy_status"):
                normalize_proxy_before_save(sender=Proxy, instance=proxy)

        self.assertEqual(proxy.url, "ss://abc@1.2.3.4:8388")


class SingleSaveTest(TestCase):
    """A create must not trigger the old chain of recursive re-saves."""

    def test_create_issues_a_single_insert(self):
        def fake_update(instance):
            instance.location = "Amsterdam"
            instance.location_country_code = "NL"
            instance.location_country = "Netherlands"
            instance.is_active = True

        proxy = Proxy(
            url="ss://YWVzLTI1Ni1nY206cGFzcw==@10.0.0.9:8388#tag",
            port=0,
            location="",
        )

        with patch(
            "proxylist.models.update_proxy_status", side_effect=fake_update
        ):
            with self.assertNumQueries(1):
                proxy.save()

        proxy.refresh_from_db()
        self.assertEqual(proxy.port, 8388)
        self.assertEqual(proxy.url, "ss://YWVzLTI1Ni1nY206cGFzcw@10.0.0.9:8388")
        self.assertEqual(proxy.location, "Amsterdam")
        self.assertTrue(proxy.is_active)
