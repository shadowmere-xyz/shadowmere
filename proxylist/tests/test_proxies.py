import json
from unittest import mock

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

fake_proxy_data = {
    "YourFuckingIPAddress": "178.163.164.199",
    "YourFuckingLocation": "Amsterdam, NH, Netherlands",
    "YourFuckingHostname": "178.163.164.199",
    "YourFuckingISP": "Random ISP",
    "YourFuckingTorExit": False,
    "YourFuckingCity": "Amsterdam",
    "YourFuckingCountry": "Netherlands",
    "YourFuckingCountryCode": "NL",
}


class ProxiesTests(APITestCase):
    fixtures = ["proxies.json"]

    def test_list_proxies(self):
        response = self.client.get(reverse("proxy-list"))
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result.get("count"), 5)
        self.assertIn("results", result)
        self.assertIn("total_pages", result)
        self.assertIn("current_page", result)
        first_element = result.get("results")[0]
        self.check_elements_in_proxy_object(proxy=first_element)

    def test_get_proxy(self):
        response = self.client.get(f'{reverse("proxy-list")}74/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.check_elements_in_proxy_object(proxy=result)

    def check_elements_in_proxy_object(self, proxy):
        self.assertIn("id", proxy)
        self.assertIn("url", proxy)
        self.assertIn("location", proxy)
        self.assertIn("location_country_code", proxy)
        self.assertIn("location_country", proxy)
        self.assertIn("ip_address", proxy)
        self.assertIn("is_active", proxy)
        self.assertIn("last_checked", proxy)
        self.assertIn("last_active", proxy)
        self.assertIn("times_checked", proxy)
        self.assertIn("times_check_succeeded", proxy)
        self.assertIn("port", proxy)

    def test_add_proxy_fails_unauthenticated(self):
        proxy_data = {"url": "ss://asas"}
        response = self.client.post(
            reverse("proxy-list"),
            json.dumps(proxy_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    @mock.patch(
        "proxylist.models.get_proxy_location",
        return_value=fake_proxy_data,
    )
    @mock.patch(
        "proxylist.proxy.get_proxy_location",
        return_value=fake_proxy_data,
    )
    def test_add_proxy_correctly(
        self, get_proxy_location_models, get_proxy_location_update
    ):
        root_user = User.objects.create_superuser("root")
        self.client.force_login(root_user)
        proxy_data = {
            "url": "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmYWtlcGFzc3dvcmQ@178.163.164.199:20465#aproxy"
        }
        response = self.client.post(
            reverse("proxy-list"),
            json.dumps(proxy_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        result = json.loads(response.content)
        self.check_elements_in_proxy_object(result)
        self.assertEqual(result.get("ip_address"), "178.163.164.199")
        self.assertEqual(result.get("port"), 20465)
        self.assertEqual(result.get("location"), "Amsterdam, NH, Netherlands")
        self.assertEqual(result.get("location_country_code"), "NL")
        self.assertEqual(result.get("location_country"), "Netherlands")
        self.assertEqual(result.get("is_active"), True)
        self.assertEqual(
            result.get("url"),
            "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmYWtlcGFzc3dvcmQ@178.163.164.199:20465",
        )
