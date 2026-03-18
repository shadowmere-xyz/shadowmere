from django.test import TestCase

from proxylist.models import Proxy
from proxylist.tasks import process_line, remove_low_quality_proxies


class RemovalTest(TestCase):
    fixtures = ["proxies.json"]

    @staticmethod
    def test_remove_low_quality_proxies():
        proxies = Proxy.objects.filter(id=41)
        assert proxies.count() == 1
        remove_low_quality_proxies()
        proxies = Proxy.objects.filter(id=41)
        assert proxies.count() == 0


class ProcessLineTest(TestCase):
    def test_rejects_vmess(self):
        assert process_line("vmess://eyJhZGQiOiIxLjIuMy40In0=", set()) is None

    def test_rejects_vless(self):
        assert process_line("vless://uuid@host:443?type=tcp#name", set()) is None

    def test_rejects_trojan(self):
        assert process_line("trojan://password@host:443#name", set()) is None

    def test_rejects_hysteria(self):
        assert process_line("hysteria://host:443", set()) is None

    def test_rejects_hy2(self):
        assert process_line("hy2://password@host:443", set()) is None

    def test_rejects_http(self):
        assert process_line("https://example.com", set()) is None

    def test_rejects_empty(self):
        assert process_line("", set()) is None

    def test_rejects_none(self):
        assert process_line(None, set()) is None
