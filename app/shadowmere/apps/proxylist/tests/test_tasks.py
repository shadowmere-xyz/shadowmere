from django.test import TestCase

from proxylist.models import Proxy
from proxylist.tasks import remove_low_quality_proxies


class RemovalTest(TestCase):
    fixtures = ["proxies.json"]

    @staticmethod
    def test_remove_low_quality_proxies():
        proxies = Proxy.objects.filter(id=41)
        assert proxies.count() == 1
        remove_low_quality_proxies()
        proxies = Proxy.objects.filter(id=41)
        assert proxies.count() == 0
