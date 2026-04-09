import base64
from unittest.mock import Mock, call, patch

from django.core.cache import cache
from django.test import TestCase
from requests.exceptions import ConnectionError, ReadTimeout, SSLError

from proxylist.models import Proxy
from proxylist.tasks import (
    PROXY_UPDATE_FIELDS,
    _check_connectivity,
    _current_task_name,
    _persist_proxy_updates,
    _run_proxy_checks,
    decode_line,
    extract_sip002_url,
    poll_subscriptions,
    remove_low_quality_proxies,
    save_proxies,
    update_status,
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


class CheckConnectivityTest(TestCase):
    @staticmethod
    def _make_response(status_code):
        resp = Mock()
        resp.status_code = status_code
        return resp

    @patch("proxylist.tasks.requests.get", side_effect=SSLError())
    def test_returns_false_on_ssl_error(self, _):
        assert _check_connectivity() is False

    @patch("proxylist.tasks.requests.get", side_effect=ConnectionError())
    def test_returns_false_on_connection_error(self, _):
        assert _check_connectivity() is False

    @patch("proxylist.tasks.requests.get", side_effect=ReadTimeout())
    def test_returns_false_on_read_timeout(self, _):
        assert _check_connectivity() is False

    @patch("proxylist.tasks.requests.get")
    def test_returns_false_on_non_204_status(self, mock_get):
        mock_get.return_value = self._make_response(200)
        with self.assertLogs("django", level="ERROR") as cm:
            result = _check_connectivity()
        assert result is False
        assert any("connection issues" in r.getMessage() for r in cm.records)

    @patch("proxylist.tasks.requests.get")
    def test_returns_true_on_204_status(self, mock_get):
        mock_get.return_value = self._make_response(204)
        with self.assertLogs("django", level="INFO") as cm:
            result = _check_connectivity()
        assert result is True
        assert any("ShadowTest" in r.getMessage() for r in cm.records)

    @patch("proxylist.tasks.requests.get", side_effect=SSLError())
    def test_logs_error_on_exception(self, _):
        with self.assertLogs("django", level="ERROR") as cm:
            _check_connectivity()
        assert any("connection issues" in r.getMessage() for r in cm.records)


class RunProxyChecksTest(TestCase):
    @patch("proxylist.tasks.update_proxy_status")
    def test_calls_update_for_each_proxy(self, mock_update):
        proxies = [Mock(spec=Proxy), Mock(spec=Proxy), Mock(spec=Proxy)]
        with self.assertLogs("django", level="INFO"):
            _run_proxy_checks(proxies)
        assert mock_update.call_count == 3
        mock_update.assert_has_calls([call(p) for p in proxies], any_order=True)

    @patch("proxylist.tasks.update_proxy_status")
    def test_handles_empty_list(self, mock_update):
        with self.assertLogs("django", level="INFO") as cm:
            _run_proxy_checks([])
        mock_update.assert_not_called()
        assert any("Proxies statuses checked" in r.getMessage() for r in cm.records)

    @patch("proxylist.tasks.update_proxy_status")
    def test_logs_completion(self, _):
        with self.assertLogs("django", level="INFO") as cm:
            _run_proxy_checks([])
        assert any("Proxies statuses checked" in r.getMessage() for r in cm.records)


class PersistProxyUpdatesTest(TestCase):
    fixtures = ["proxies.json"]

    @staticmethod
    def test_returns_zero_for_empty_list():
        assert _persist_proxy_updates([]) == 0

    @staticmethod
    def test_does_not_touch_db_for_empty_list():
        before = Proxy.objects.count()
        _persist_proxy_updates([])
        assert Proxy.objects.count() == before

    @staticmethod
    def test_does_not_clear_cache_for_empty_list():
        cache.set("sentinel", "value")
        _persist_proxy_updates([])
        assert cache.get("sentinel") == "value"

    @staticmethod
    def test_returns_count_of_saved_proxies():
        proxies = list(Proxy.objects.all()[:2])
        result = _persist_proxy_updates(proxies)
        assert result == 2

    @staticmethod
    def test_bulk_updates_with_correct_fields():
        proxies = list(Proxy.objects.all()[:1])
        with patch.object(Proxy.objects.__class__, "bulk_update") as mock_bulk:
            _persist_proxy_updates(proxies)
        mock_bulk.assert_called_once_with(proxies, PROXY_UPDATE_FIELDS, batch_size=500)

    @staticmethod
    def test_clears_cache_after_update():
        cache.set("sentinel", "value")
        proxies = list(Proxy.objects.all()[:1])
        _persist_proxy_updates(proxies)
        assert cache.get("sentinel") is None


class UpdateStatusTest(TestCase):
    fixtures = ["proxies.json"]

    @patch("proxylist.tasks._check_connectivity", return_value=False)
    def test_returns_early_when_not_connected(self, _):
        with patch("proxylist.tasks.Proxy") as mock_proxy:
            update_status()
        mock_proxy.objects.all.assert_not_called()

    @patch("proxylist.tasks._check_connectivity", return_value=False)
    def test_logs_start_even_when_not_connected(self, _):
        with self.assertLogs("django", level="INFO") as cm:
            update_status()
        assert any("Updating proxies status" in r.getMessage() for r in cm.records)

    @patch("proxylist.tasks._persist_proxy_updates", return_value=3)
    @patch("proxylist.tasks._run_proxy_checks")
    @patch("proxylist.tasks._check_connectivity", return_value=True)
    def test_runs_checks_and_persists_when_connected(self, _, mock_run, mock_persist):
        with self.assertLogs("django", level="INFO"):
            update_status()
        mock_run.assert_called_once()
        mock_persist.assert_called_once()

    @patch("proxylist.tasks._persist_proxy_updates", return_value=5)
    @patch("proxylist.tasks._run_proxy_checks")
    @patch("proxylist.tasks._check_connectivity", return_value=True)
    def test_logs_completion_with_saved_count(self, _, _run, _persist):
        with self.assertLogs("django", level="INFO") as cm:
            update_status()
        record = next(r for r in cm.records if "Update completed" in r.getMessage())
        assert record.saved == 5

    @patch("proxylist.tasks._persist_proxy_updates", return_value=0)
    @patch("proxylist.tasks._run_proxy_checks")
    @patch("proxylist.tasks._check_connectivity", return_value=True)
    def test_passes_all_proxies_to_run_checks(self, _, mock_run, _persist):
        with self.assertLogs("django", level="INFO"):
            update_status()
        proxies_arg = mock_run.call_args[0][0]
        assert len(proxies_arg) == Proxy.objects.count()


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
