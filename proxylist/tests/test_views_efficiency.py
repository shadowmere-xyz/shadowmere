from types import SimpleNamespace

from django.test import TestCase

from proxylist.models import Proxy
from proxylist.views import get_proxy_config


class HomepageCountTest(TestCase):
    fixtures = ["proxies.json"]

    def test_context_exposes_scalar_count_not_full_queryset(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        expected = Proxy.objects.filter(is_active=True).count()
        self.assertEqual(response.context["proxy_count"], expected)
        # The full unpaginated queryset must not be handed to the template.
        self.assertNotIn("proxy_list", response.context)

    def test_page_obj_is_paginated(self):
        response = self.client.get("/")

        page_obj = response.context["page_obj"]
        self.assertLessEqual(len(page_obj), 15)


class GetProxyConfigTest(TestCase):
    @staticmethod
    def _proxy(url):
        return SimpleNamespace(url=url, location_country_code="", location="Somewhere")

    def test_parses_method_server_port_and_password(self):
        # base64("aes-256-gcm:secret") = YWVzLTI1Ni1nY206c2VjcmV0
        proxy = self._proxy("ss://YWVzLTI1Ni1nY206c2VjcmV0@1.2.3.4:8388")

        config = get_proxy_config(proxy)

        self.assertEqual(config["method"], "aes-256-gcm")
        self.assertEqual(config["password"], "secret")
        self.assertEqual(config["server"], "1.2.3.4")
        self.assertEqual(config["server_port"], 8388)

    def test_password_with_colon_is_preserved(self):
        # base64("aes-256-gcm:pass:word") = YWVzLTI1Ni1nY206cGFzczp3b3Jk
        proxy = self._proxy("ss://YWVzLTI1Ni1nY206cGFzczp3b3Jk@1.2.3.4:8388")

        config = get_proxy_config(proxy)

        self.assertEqual(config["method"], "aes-256-gcm")
        self.assertEqual(config["password"], "pass:word")
