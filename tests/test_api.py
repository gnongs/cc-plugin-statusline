import json
import time

import pytest

from statusline import api


@pytest.fixture
def cache_path(tmp_path):
    return str(tmp_path / "usage.json")


def _write(path, data, ts):
    with open(path, "w") as f:
        json.dump({"data": data, "ts": ts}, f)


class TestReadStaleCache:
    def test_returns_data_within_max_age(self, cache_path):
        _write(cache_path, {"ok": 1}, ts=time.time() - 60)
        assert api._read_stale_cache(cache_path) == {"ok": 1}

    def test_drops_data_beyond_default_max_age(self, cache_path):
        """Default STALE_MAX_AGE should reject caches older than 30 minutes."""
        _write(cache_path, {"ok": 1}, ts=time.time() - 3600)
        assert api._read_stale_cache(cache_path) is None

    def test_respects_explicit_max_age(self, cache_path):
        _write(cache_path, {"ok": 1}, ts=time.time() - 120)
        assert api._read_stale_cache(cache_path, max_age=60) is None
        assert api._read_stale_cache(cache_path, max_age=300) == {"ok": 1}

    def test_max_age_none_disables_limit(self, cache_path):
        """Passing None explicitly should return data regardless of age (opt-out)."""
        _write(cache_path, {"ok": 1}, ts=time.time() - 99999)
        assert api._read_stale_cache(cache_path, max_age=None) == {"ok": 1}

    def test_missing_file_returns_none(self, tmp_path):
        assert api._read_stale_cache(str(tmp_path / "missing.json")) is None


class TestUsageResetExpired:
    def test_future_resets_at_is_not_expired(self):
        future = time.time() + 3600
        assert api._usage_reset_expired({"five_hour": {"resets_at": future}}) is False

    def test_past_unix_timestamp_is_expired(self):
        past = time.time() - 60
        assert api._usage_reset_expired({"five_hour": {"resets_at": past}}) is True

    def test_past_iso_string_is_expired(self):
        assert api._usage_reset_expired(
            {"seven_day": {"resets_at": "2000-01-01T00:00:00Z"}}
        ) is True

    def test_future_iso_string_is_not_expired(self):
        assert api._usage_reset_expired(
            {"seven_day": {"resets_at": "2099-01-01T00:00:00Z"}}
        ) is False

    def test_expired_in_either_bucket_propagates(self):
        data = {
            "five_hour": {"resets_at": time.time() + 3600},
            "seven_day": {"resets_at": "2000-01-01T00:00:00Z"},
        }
        assert api._usage_reset_expired(data) is True

    def test_none_or_empty_data_is_not_expired(self):
        assert api._usage_reset_expired(None) is False
        assert api._usage_reset_expired({}) is False

    def test_malformed_resets_at_is_ignored(self):
        assert api._usage_reset_expired(
            {"five_hour": {"resets_at": "garbage"}}
        ) is False


class TestFetchUsageInvalidation:
    def _fresh_cache(self, path, resets_at):
        api._write_cache(path, {
            "five_hour": {"utilization": 50, "resets_at": resets_at},
        })

    def test_uses_cache_when_resets_at_future(self, monkeypatch, tmp_path):
        cache = str(tmp_path / "usage.json")
        monkeypatch.setattr(api, "USAGE_CACHE", cache)
        future = time.time() + 3600
        self._fresh_cache(cache, future)

        calls = []
        monkeypatch.setattr(api, "get_oauth_token", lambda: "tok")
        monkeypatch.setattr(api, "_curl_api", lambda *a, **k: calls.append(a) or None)

        data = api.fetch_usage()
        assert data["five_hour"]["utilization"] == 50
        assert calls == [], "cached value should be returned without refetch"

    def test_refetches_when_cached_resets_at_is_past(self, monkeypatch, tmp_path):
        cache = str(tmp_path / "usage.json")
        monkeypatch.setattr(api, "USAGE_CACHE", cache)
        self._fresh_cache(cache, time.time() - 60)

        fresh = {"five_hour": {"utilization": 5, "resets_at": time.time() + 3600}}
        calls = []

        def fake_curl(*a, **k):
            calls.append(a)
            return fresh

        monkeypatch.setattr(api, "get_oauth_token", lambda: "tok")
        monkeypatch.setattr(api, "_curl_api", fake_curl)

        data = api.fetch_usage()
        assert len(calls) == 1, "expired resets_at must trigger a refetch"
        assert data["five_hour"]["utilization"] == 5
