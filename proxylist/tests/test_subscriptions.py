import json

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase

from proxylist.models import Subscription
from proxylist.tests.test_proxies import APPLICATION_JSON_CONTENT_TYPE


class SubscriptionssTests(APITestCase):
    fixtures = ["subscriptions.json"]

    def test_list_subscriptions(self):
        root_user = User.objects.create_superuser("root")
        self.client.force_login(root_user)

        response = self.client.get(reverse("subscription-list"))
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result.get("count"), 2)
        self.assertIn("results", result)
        first_element = result.get("results")[0]
        self.check_elements_in_subscription_object(subscription=first_element)

    def test_get_subscription(self):
        root_user = User.objects.create_superuser("root")
        self.client.force_login(root_user)
        response = self.client.get(f'{reverse("subscription-list")}6/')
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.check_elements_in_subscription_object(subscription=result)

    def check_elements_in_subscription_object(self, subscription):
        self.assertIn("url", subscription)
        self.assertIn("kind", subscription)

    def test_add_subscription_fails_unauthenticated(self):
        subscription_data = {"url": "http://example.com/sub", "kind": "standard"}
        response = self.client.post(
            reverse("subscription-list"),
            json.dumps(subscription_data),
            content_type=APPLICATION_JSON_CONTENT_TYPE,
        )
        self.assertEqual(response.status_code, 403)

    def test_add_subscription(self):
        root_user = User.objects.create_superuser("root")
        self.client.force_login(root_user)
        subscription_data = {"url": "http://example.com/sub", "kind": "PLAIN"}
        response = self.client.post(
            reverse("subscription-list"),
            json.dumps(subscription_data),
            content_type=APPLICATION_JSON_CONTENT_TYPE,
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Subscription.objects.count(), 3)
        result = json.loads(response.content)
        self.check_elements_in_subscription_object(subscription=result)

    def test_add_subscription_fails_wrong_kind(self):
        root_user = User.objects.create_superuser("root")
        self.client.force_login(root_user)
        subscription_data = {"url": "http://example.com/sub", "kind": "INVALID_KIND"}
        response = self.client.post(
            reverse("subscription-list"),
            json.dumps(subscription_data),
            content_type=APPLICATION_JSON_CONTENT_TYPE,
        )
        self.assertEqual(response.status_code, 400)
