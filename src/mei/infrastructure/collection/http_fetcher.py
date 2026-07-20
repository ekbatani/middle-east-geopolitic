import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from mei.shared.config import get_settings
from mei.shared.errors import FetchError, UnsupportedURLError

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_CONTENT_TYPE_PREFIXES = (
    "text/html",
    "application/xhtml+xml",
    "text/plain",
    "application/xml",
    "text/xml",
    "application/rss+xml",
    "application/atom+xml",
)
MAX_REDIRECTS = 5
MAX_RESPONSE_BYTES = 20 * 1024 * 1024
CONNECT_TIMEOUT_SECONDS = 10.0
READ_TIMEOUT_SECONDS = 20.0
USER_AGENT = "mei-collector/0.1 (+https://mei.dev)"


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int
    content_type: str
    body: bytes


def validate_url_security(url: str) -> None:
    """Reject URLs the SSRF policy in design doc section 10.3 disallows.

    Raises `UnsupportedURLError` rather than returning a bool so every call
    site fails closed instead of forgetting to check a return value.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise UnsupportedURLError(f"Scheme '{parsed.scheme}' is not allowed; use http or https")
    if not parsed.hostname:
        raise UnsupportedURLError("URL is missing a hostname")

    allowed_hosts = frozenset(get_settings().collector_allowed_private_hosts)
    if parsed.hostname in allowed_hosts:
        return

    try:
        addrinfo = socket.getaddrinfo(parsed.hostname, None)
    except OSError as exc:
        raise UnsupportedURLError(f"Could not resolve host '{parsed.hostname}'") from exc

    for _family, _type, _proto, _canonname, sockaddr in addrinfo:
        ip = ipaddress.ip_address(sockaddr[0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise UnsupportedURLError(f"URL resolves to a disallowed address range ({ip})")


async def fetch_url(url: str) -> FetchResult:
    """Fetch a single URL under the SSRF-safe policy, following redirects manually.

    Every hop (including the initial URL) is re-validated before it is
    requested, since a redirect target is attacker-controlled input.
    """
    current_url = url
    timeout = httpx.Timeout(READ_TIMEOUT_SECONDS, connect=CONNECT_TIMEOUT_SECONDS)

    async with httpx.AsyncClient(follow_redirects=False, timeout=timeout) as client:
        for _ in range(MAX_REDIRECTS + 1):
            validate_url_security(current_url)
            try:
                async with client.stream(
                    "GET", current_url, headers={"User-Agent": USER_AGENT}
                ) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise FetchError("Redirect response missing Location header")
                        current_url = str(response.url.join(location))
                        continue

                    if response.status_code >= 400:
                        raise FetchError(
                            f"Fetch failed with status {response.status_code} for {current_url}"
                        )

                    content_type = (
                        response.headers.get("content-type", "").split(";")[0].strip().lower()
                    )
                    if content_type and not content_type.startswith(ALLOWED_CONTENT_TYPE_PREFIXES):
                        raise UnsupportedURLError(f"Unsupported content type: {content_type}")

                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_RESPONSE_BYTES:
                            raise FetchError("Response exceeded maximum allowed size")

                    return FetchResult(
                        url=str(response.url),
                        status_code=response.status_code,
                        content_type=content_type,
                        body=bytes(body),
                    )
            except httpx.HTTPError as exc:
                raise FetchError(f"HTTP request failed for {current_url}: {exc}") from exc

    raise FetchError(f"Too many redirects starting from {url}")


__all__ = ["FetchResult", "fetch_url", "validate_url_security"]
