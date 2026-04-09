import base64

from django.test import TestCase

from proxylist.models import Proxy
from proxylist.tasks import decode_line, extract_sip002_url, process_line, remove_low_quality_proxies


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
    @staticmethod
    def test_rejects_vmess():
        assert process_line("vmess://eyJhZGQiOiIxLjIuMy40In0=", set()) is None

    @staticmethod
    def test_rejects_vless():
        assert process_line("vless://uuid@host:443?type=tcp#name", set()) is None

    @staticmethod
    def test_rejects_trojan():
        assert process_line("trojan://password@host:443#name", set()) is None

    @staticmethod
    def test_rejects_hysteria():
        assert process_line("hysteria://host:443", set()) is None

    @staticmethod
    def test_rejects_hy2():
        assert process_line("hy2://password@host:443", set()) is None

    @staticmethod
    def test_rejects_http():
        assert process_line("https://example.com", set()) is None

    @staticmethod
    def test_rejects_empty():
        assert process_line("", set()) is None

    @staticmethod
    def test_rejects_none():
        assert process_line(None, set()) is None


class ExtractSip002UrlTest(TestCase):
    @staticmethod
    def test_rejects_vmess():
        assert extract_sip002_url("vmess://eyJhZGQiOiIxLjIuMy40In0=", set()) is None

    @staticmethod
    def test_rejects_vless():
        assert extract_sip002_url("vless://uuid@host:443?type=tcp#name", set()) is None

    @staticmethod
    def test_rejects_trojan():
        assert extract_sip002_url("trojan://password@host:443#name", set()) is None

    @staticmethod
    def test_rejects_http():
        assert extract_sip002_url("https://example.com", set()) is None

    @staticmethod
    def test_rejects_empty():
        assert extract_sip002_url("", set()) is None

    @staticmethod
    def test_rejects_none():
        assert extract_sip002_url(None, set()) is None

    @staticmethod
    def test_rejects_already_known_url():
        url = "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpwYXNz@1.2.3.4:8388"
        assert extract_sip002_url(url, {url}) is None

    @staticmethod
    def test_returns_url_for_unknown_ss_address():
        # A minimal valid ss:// URL that get_sip002 can normalize
        line = "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpwYXNz@1.2.3.4:8388"
        result = extract_sip002_url(line, set())
        # Should return a non-empty string (the normalized URL)
        assert result is not None
        assert result.startswith("ss://")


class DecodeLineTest(TestCase):
    @staticmethod
    def test_valid_utf8_bytes():
        content = "line1\nline2\nline3"
        encoded = base64.b64encode(content.encode("utf-8"))
        result = decode_line(encoded)
        assert result == ["line1", "line2", "line3"]

    @staticmethod
    def test_valid_utf8_str():
        content = "hello\nworld"
        encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
        result = decode_line(encoded)
        assert result == ["hello", "world"]

    @staticmethod
    def test_single_line():
        content = "ss://method:password@host:1234"
        encoded = base64.b64encode(content.encode("utf-8"))
        result = decode_line(encoded)
        assert result == [content]

    @staticmethod
    def test_empty_content():
        encoded = base64.b64encode(b"")
        result = decode_line(encoded)
        assert result == [""]

    @staticmethod
    def test_empty_bytes():
        result = decode_line(b"")
        assert result == [""]

    @staticmethod
    def test_empty_str():
        result = decode_line("")
        assert result == [""]

    @staticmethod
    def test_invalid_base64():
        result = decode_line(b"!!!not-base64$$$")
        assert result is None

    @staticmethod
    def test_missing_padding():
        content = "test"
        encoded = base64.b64encode(content.encode("utf-8")).rstrip(b"=")
        result = decode_line(encoded)
        assert result == ["test"]

    @staticmethod
    def test_non_utf8_bytes_replaced():
        raw = b"hello\xff\xfeworld"
        encoded = base64.b64encode(raw)
        result = decode_line(encoded)
        assert result is not None
        joined = result[0]
        assert "hello" in joined
        assert "world" in joined
        assert "\ufffd" in joined

    @staticmethod
    def test_latin1_content():
        raw = "café".encode("latin-1")
        encoded = base64.b64encode(raw)
        result = decode_line(encoded)
        assert result is not None
        assert len(result) >= 1

    @staticmethod
    def test_multiline_with_empty_lines():
        content = "a\n\nb\n\nc"
        encoded = base64.b64encode(content.encode("utf-8"))
        result = decode_line(encoded)
        assert result == ["a", "", "b", "", "c"]

    @staticmethod
    def test_trailing_newline():
        content = "line1\nline2\n"
        encoded = base64.b64encode(content.encode("utf-8"))
        result = decode_line(encoded)
        assert result == ["line1", "line2", ""]

    @staticmethod
    def test_unicode_content():
        content = "日本語\n中文\nрусский"
        encoded = base64.b64encode(content.encode("utf-8"))
        result = decode_line(encoded)
        assert result == ["日本語", "中文", "русский"]

    @staticmethod
    def test_url_safe_base64_chars():
        content = "ss://Y2hhY2hhMjA@1.2.3.4:8388"
        encoded = base64.b64encode(content.encode("utf-8"))
        result = decode_line(encoded)
        assert result == [content]

    @staticmethod
    def test_windows_line_endings():
        content = "line1\r\nline2\r\n"
        encoded = base64.b64encode(content.encode("utf-8"))
        result = decode_line(encoded)
        assert result is not None
        assert "line1" in result[0]

    @staticmethod
    def test_large_input():
        content = "\n".join(f"ss://proxy{i}" for i in range(1000))
        encoded = base64.b64encode(content.encode("utf-8"))
        result = decode_line(encoded)
        assert result is not None
        assert len(result) == 1000
