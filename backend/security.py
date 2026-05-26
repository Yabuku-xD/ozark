import ipaddress
import os
import socket
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ALLOWED_TRACE_ROOTS = [ROOT, Path.cwd(), Path('/tmp')]


def validate_live_endpoint(endpoint: str) -> None:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Live endpoint must use http or https")
    if not parsed.hostname:
        raise ValueError("Live endpoint must include a hostname")

    allowlist = _csv_env("OZARK_ALLOWED_ENDPOINT_HOSTS")
    if allowlist and parsed.hostname not in allowlist:
        raise ValueError(f"Endpoint host is not allowlisted: {parsed.hostname}")

    if os.environ.get("OZARK_ALLOW_PRIVATE_ENDPOINTS", "1") == "1":
        return

    for ip in _resolve_host_ips(parsed.hostname, parsed.port or 80):
        if _is_blocked_ip(ip):
            raise ValueError(f"Endpoint resolves to blocked internal address: {ip}")


def validate_trace_path(path: str) -> Path:
    candidate = Path(path).expanduser().resolve()
    if not candidate.exists():
        raise FileNotFoundError(f"Trace file not found: {path}")
    allowed = [Path(p).expanduser().resolve() for p in _csv_env("OZARK_ALLOWED_TRACE_ROOTS")]
    if not allowed:
        allowed = [root.resolve() for root in DEFAULT_ALLOWED_TRACE_ROOTS]
    if not any(candidate == root or root in candidate.parents for root in allowed):
        roots = ", ".join(str(root) for root in allowed)
        raise ValueError(f"Trace path is outside allowed roots: {roots}")
    return candidate


def _resolve_host_ips(hostname: str, port: int) -> set[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    return {ipaddress.ip_address(addr[4][0]) for addr in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)}


def _is_blocked_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return ip.is_private or ip.is_loopback or ip.is_link_local or getattr(ip, "is_reserved", False)


def _csv_env(name: str) -> list[str]:
    value = os.environ.get(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]
