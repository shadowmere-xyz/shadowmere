import base64
from unittest.mock import Mock, patch

from django.test import TestCase

from proxylist.models import Proxy
from proxylist.tasks import (
    _current_task_name,
    decode_line,
    extract_sip002_url,
    poll_subscriptions,
    remove_low_quality_proxies,
    save_proxies,
)


class CurrentTaskNameTest(TestCase):
    @staticmethod
    def test_unknown_when_called_outside_tasks_module():
        assert _current_task_name() == "unknown"

    def test_returns_direct_entry_point(self):
        with self.assertLogs("django", level="INFO") as cm:
            save_proxies([])
        record = next(r for r in cm.records if "Saving proxies" in r.getMessage())
        assert record.task == "save_proxies"

    def test_outermost_frame_wins_when_nested(self):
        with self.assertLogs("django", level="INFO") as cm:
            poll_subscriptions()
        record = next(r for r in cm.records if "Saving proxies" in r.getMessage())
        assert record.task == "poll_subscriptions"


class RemovalTest(TestCase):
    fixtures = ["proxies.json"]

    @staticmethod
    def test_remove_low_quality_proxies():
        proxies = Proxy.objects.filter(id=41)
        assert proxies.count() == 1
        remove_low_quality_proxies()
        proxies = Proxy.objects.filter(id=41)
        assert proxies.count() == 0


class ExtractSip002UrlTest(TestCase):
    @staticmethod
    def test_rejects_vmess():
        assert extract_sip002_url("vmess://eyJhZGQiOiIxLjIuMy40In0=") is None

    @staticmethod
    def test_rejects_vless():
        assert extract_sip002_url("vless://uuid@host:443?type=tcp#name") is None

    @staticmethod
    def test_rejects_trojan():
        assert extract_sip002_url("trojan://password@host:443#name") is None

    @staticmethod
    def test_rejects_hysteria():
        assert extract_sip002_url("hysteria://host:443") is None

    @staticmethod
    def test_rejects_hy2():
        assert extract_sip002_url("hy2://password@host:443") is None

    @staticmethod
    def test_rejects_tuic():
        assert extract_sip002_url("tuic://uuid:password@host:443") is None

    @staticmethod
    def test_rejects_http():
        assert extract_sip002_url("http://example.com") is None

    @staticmethod
    def test_rejects_https():
        assert extract_sip002_url("https://example.com") is None

    @staticmethod
    def test_rejects_empty():
        assert extract_sip002_url("") is None

    @staticmethod
    def test_rejects_none():
        assert extract_sip002_url(None) is None

    @staticmethod
    def test_returns_url_for_valid_ss_address():
        line = "ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpwYXNz@1.2.3.4:8388"
        result = extract_sip002_url(line)
        assert result is not None
        assert result.startswith("ss://")


class PollSubscriptionsDeduplicationTest(TestCase):
    fixtures = ["proxies.json", "subscriptions.json"]

    DB_URL = "ss://YWVzLTI1Ni1nY206UENubkg2U1FTbmZvUzI3@172.105.42.160:8091"

    SHARED_URL = "ss://aes-256-gcm:shared-password@10.0.0.1:8388"
    UNIQUE_URL_1 = "ss://aes-256-gcm:unique-one@10.0.0.2:8388"
    UNIQUE_URL_2 = "ss://aes-256-gcm:unique-two@10.0.0.3:8388"

    def _plain_response(self):
        resp = Mock()
        resp.status_code = 200
        resp.iter_lines.return_value = [
            self.UNIQUE_URL_1.encode(),
            self.SHARED_URL.encode(),
            self.DB_URL.encode(),
        ]
        return resp

    def _base64_response(self):
        content = "\n".join(
            [
                self.SHARED_URL,
                self.SHARED_URL,
                self.UNIQUE_URL_2,
                self.DB_URL,
            ]
        ).encode()
        resp = Mock()
        resp.status_code = 200
        resp.iter_lines.return_value = [base64.b64encode(content)]
        return resp

    def test_deduplication_and_db_filtering(self):
        plain_response = self._plain_response()
        b64_response = self._base64_response()

        def requests_side_effect(url, **kwargs):
            if url == "https://a.proxy.xyz/sip002/sub":
                return b64_response
            if url == "https://raw.githubusercontent.com/a/sub.txt":
                return plain_response
            raise ValueError(f"Unexpected subscription URL in test: {url}")

        def mock_update_proxy_status(proxy):
            proxy.location = "Mocked Location"
            proxy.is_active = True

        initial_count = Proxy.objects.count()

        with (
            patch("requests.get", side_effect=requests_side_effect),
            patch(
                "proxylist.tasks.get_proxy_location", return_value="Tokyo, Japan"
            ) as mock_loc,
            patch(
                "proxylist.models.update_proxy_status",
                side_effect=mock_update_proxy_status,
            ),
        ):
            poll_subscriptions()

        tested_urls = {c.args[0] for c in mock_loc.call_args_list}
        assert tested_urls == {self.SHARED_URL, self.UNIQUE_URL_1, self.UNIQUE_URL_2}
        assert self.DB_URL not in tested_urls

        assert Proxy.objects.count() == initial_count + 3
        assert Proxy.objects.filter(url=self.SHARED_URL).exists()
        assert Proxy.objects.filter(url=self.UNIQUE_URL_1).exists()
        assert Proxy.objects.filter(url=self.UNIQUE_URL_2).exists()
        assert Proxy.objects.filter(url=self.DB_URL).count() == 1


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
