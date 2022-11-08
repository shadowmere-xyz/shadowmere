import json

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase


class PortsEndpointTests(APITestCase):
    fixtures = ["proxies.json"]

    def test_ports(self):
        response = self.client.get(reverse("ports-list"))
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result, [{"port": 807}, {"port": 2375}, {"port": 8091}])


class CountryCodesEndpointTests(APITestCase):
    fixtures = ["proxies.json"]

    def test_country_codes(self):
        response = self.client.get(reverse("country-codes-list"))
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(
            result,
            [
                {"code": "NL", "name": "Netherlands"},
                {"code": "SE", "name": "Sweden"},
                {"code": "US", "name": "United States"},
            ],
        )


class QRGenerationTest(TestCase):
    fixtures = ["proxies.json"]

    def test_qr_generated_correctly(self):
        response = self.client.get("/74/qr")
        self.assertEqual(
            response.status_code,
            200,
            "qr generation failed",
        )
        self.assertEqual(response.headers.get("Content-Type"), "image/png")
        self.assertEqual(
            response.headers.get("Content-Disposition"),
            'attachment; filename="qr_74.png"',
        )

    def test_qr_inexistent_proxy_fails(self):
        response = self.client.get("/20/qr")
        self.assertEqual(
            response.status_code,
            404,
            "qr generation for non existent proxy should return Not Found",
        )


class SubEndpointTests(APITestCase):
    fixtures = ["proxies.json"]

    def test_get_sub(self):
        response = self.client.get(reverse("sub-list"))
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(
            result,
            [
                {
                    "method": "chacha20-ietf-poly1305",
                    "password": "ppmyIUP2euYM",
                    "plugin": "",
                    "plugin_opts": None,
                    "remarks": "Waalwijk, NB, Netherlands",
                    "server": "37.218.242.73",
                    "server_port": 8091,
                },
                {
                    "method": "chacha20-ietf-poly1305",
                    "password": "G!yBwPWH3Vao",
                    "plugin": "",
                    "plugin_opts": None,
                    "remarks": "Stockholm, AB, Sweden",
                    "server": "196.196.156.122",
                    "server_port": 807,
                },
                {
                    "method": "aes-256-gcm",
                    "password": "faBAoD54k87UJG7",
                    "plugin": "",
                    "plugin_opts": None,
                    "remarks": "unknown",
                    "server": "169.197.142.39",
                    "server_port": 2375,
                },
            ],
        )
