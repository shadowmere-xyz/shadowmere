import json

from django.urls import reverse
from rest_framework.test import APITestCase

from proxylist.base64_decoder import decode_base64


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
                    "remarks": "🇳🇱 Waalwijk, NB, Netherlands",
                    "server": "37.218.242.73",
                    "server_port": 8091,
                },
                {
                    "method": "chacha20-ietf-poly1305",
                    "password": "G!yBwPWH3Vao",
                    "plugin": "",
                    "plugin_opts": None,
                    "remarks": "🇸🇪 Stockholm, AB, Sweden",
                    "server": "196.196.156.122",
                    "server_port": 807,
                },
                {
                    "method": "aes-256-gcm",
                    "password": "faBAoD54k87UJG7",
                    "plugin": "",
                    "plugin_opts": None,
                    "remarks": "🇺🇸 unknown",
                    "server": "169.197.142.39",
                    "server_port": 2375,
                },
            ],
        )

    def test_get_b64sub(self):
        response = self.client.get(reverse("b64sub-list"))
        self.assertEqual(response.status_code, 200)
        content = decode_base64(response.content).decode("utf-8")
        assert (
            content
            == "\nss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpwcG15SVVQMmV1WU0@37.218.242.73:8091#🇳🇱 Waalwijk, NB, Netherlands\nss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpHIXlCd1BXSDNWYW8@196.196.156.122:807#🇸🇪 Stockholm, AB, Sweden\nss://YWVzLTI1Ni1nY206ZmFCQW9ENTRrODdVSkc3@169.197.142.39:2375#🇺🇸 unknown"
        )
