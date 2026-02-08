import json
import os
import subprocess
import sys
import time

CACHE_DIR = "/tmp/claude_statusline"
USAGE_CACHE = os.path.join(CACHE_DIR, "usage.json")
PROFILE_CACHE = os.path.join(CACHE_DIR, "profile.json")
USAGE_TTL = 60
PROFILE_TTL = 3600


def get_oauth_token():
    """Get OAuth token from macOS Keychain or ~/.claude/.credentials.json."""
    # macOS Keychain
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0:
                creds = json.loads(result.stdout.strip())
                token = creds.get("claudeAiOauth", {}).get("accessToken")
                if token:
                    return token
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

    # Fallback: credentials file (Linux/Windows)
    try:
        cred_path = os.path.join(os.path.expanduser("~"), ".claude", ".credentials.json")
        if os.path.exists(cred_path):
            with open(cred_path, 'r') as f:
                creds = json.load(f)
            return creds.get("claudeAiOauth", {}).get("accessToken")
    except Exception:
        pass

    return None


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _read_cache(path, ttl):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                cache = json.load(f)
            if time.time() - cache.get("ts", 0) < ttl:
                return cache.get("data")
    except Exception:
        pass
    return None


def _read_stale_cache(path):
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f).get("data")
    except Exception:
        pass
    return None


def _write_cache(path, data):
    try:
        _ensure_cache_dir()
        with open(path, 'w') as f:
            json.dump({"data": data, "ts": time.time()}, f)
    except Exception:
        pass


def _curl_api(endpoint, token):
    """Call Anthropic API via curl (avoids Python SSL issues on macOS)."""
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5",
             "-H", "Accept: application/json",
             "-H", f"Authorization: Bearer {token}",
             "-H", "anthropic-beta: oauth-2025-04-20",
             f"https://api.anthropic.com/api/{endpoint}"],
            capture_output=True, text=True, timeout=8
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return None


def fetch_usage():
    cached = _read_cache(USAGE_CACHE, USAGE_TTL)
    if cached:
        return cached
    token = get_oauth_token()
    if not token:
        return _read_stale_cache(USAGE_CACHE)
    data = _curl_api("oauth/usage", token)
    if data and "five_hour" in data:
        _write_cache(USAGE_CACHE, data)
        return data
    return _read_stale_cache(USAGE_CACHE)


def fetch_profile():
    cached = _read_cache(PROFILE_CACHE, PROFILE_TTL)
    if cached:
        return cached
    token = get_oauth_token()
    if not token:
        return _read_stale_cache(PROFILE_CACHE)
    data = _curl_api("oauth/profile", token)
    if data and "account" in data:
        _write_cache(PROFILE_CACHE, data)
        return data
    return _read_stale_cache(PROFILE_CACHE)
