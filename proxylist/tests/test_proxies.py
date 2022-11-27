import json

from django.urls import reverse
from rest_framework.test import APITestCase


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
