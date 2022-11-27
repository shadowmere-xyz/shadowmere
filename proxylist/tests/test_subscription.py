import json

from django.urls import reverse
from rest_framework.test import APITestCase


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
