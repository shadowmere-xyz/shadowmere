import json

from django.urls import reverse
from rest_framework.test import APITestCase


class MessagesProcessingTests(APITestCase):
    fixtures = ["proxies.json"]

    def test_empty_ports(self):
        response = self.client.get(reverse('ports'))
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result, [807, 2375, 8091])
