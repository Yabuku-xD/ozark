"""Tests for security controls (security.py).

Covers SSRF protection defaults, private-endpoint blocking, and
trace-path confinement.
"""

from __future__ import annotations

import pytest

from backend import security


def test_private_endpoint_blocked_by_default(monkeypatch):
    # SSRF protection is ON by default (OZARK_ALLOW_PRIVATE_ENDPOINTS unset).
    monkeypatch.delenv("OZARK_ALLOW_PRIVATE_ENDPOINTS", raising=False)
    monkeypatch.delenv("OZARK_ALLOWED_ENDPOINT_HOSTS", raising=False)
    with pytest.raises(ValueError, match="blocked internal address"):
        security.validate_live_endpoint("http://127.0.0.1:8080")
    with pytest.raises(ValueError, match="blocked internal address"):
        security.validate_live_endpoint("http://localhost:8080")


def test_private_endpoint_allowed_when_opted_in(monkeypatch):
    monkeypatch.setenv("OZARK_ALLOW_PRIVATE_ENDPOINTS", "1")
    # Should not raise — opt-in disables the private-IP check.
    security.validate_live_endpoint("http://127.0.0.1:8080")


def test_invalid_scheme_rejected(monkeypatch):
    monkeypatch.delenv("OZARK_ALLOW_PRIVATE_ENDPOINTS", raising=False)
    with pytest.raises(ValueError, match="http or https"):
        security.validate_live_endpoint("file:///etc/passwd")


def test_host_allowlist_enforced(monkeypatch):
    monkeypatch.setenv("OZARK_ALLOWED_ENDPOINT_HOSTS", "allowed.example.com")
    with pytest.raises(ValueError, match="not allowlisted"):
        security.validate_live_endpoint("http://evil.example.com")


def test_trace_path_confined_to_project_root(tmp_path, monkeypatch):
    # A file under the project root should be allowed.
    safe_file = security.ROOT / "examples" / "prod-traces.jsonl"
    if safe_file.exists():
        result = security.validate_trace_path(str(safe_file))
        assert result == safe_file.resolve()

    # A file in an arbitrary temp dir should be rejected.
    outside = tmp_path / "evil.jsonl"
    outside.write_text("{}")
    with pytest.raises(ValueError, match="outside allowed roots"):
        security.validate_trace_path(str(outside))


def test_trace_path_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        security.validate_trace_path(str(tmp_path / "nonexistent.jsonl"))
