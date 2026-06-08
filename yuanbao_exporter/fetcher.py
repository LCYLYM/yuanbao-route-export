from __future__ import annotations

import logging
import socket
import urllib.error
import urllib.request


LOGGER = logging.getLogger(__name__)


class FetchError(RuntimeError):
    pass


class YuanbaoClient:
    def __init__(
        self,
        *,
        timeout_seconds: float = 30,
        proxy_url: str | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.proxy_url = proxy_url
        handlers: list[urllib.request.BaseHandler] = []
        if proxy_url:
            handlers.append(
                urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
            )
        self._opener = urllib.request.build_opener(*handlers)

    def fetch_html(self, url: str) -> str:
        request = urllib.request.Request(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "identity",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
                "Cache-Control": "no-cache",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"
                ),
            },
            method="GET",
        )
        try:
            LOGGER.info("fetching yuanbao share page: %s", url)
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                status = getattr(response, "status", 200)
                if status < 200 or status >= 300:
                    raise FetchError(f"HTTP 状态码异常：{status}")
                raw = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
        except urllib.error.HTTPError as exc:
            raise FetchError(f"HTTP 状态码异常：{exc.code}") from exc
        except urllib.error.URLError as exc:
            raise FetchError(f"网络请求失败：{exc.reason}") from exc
        except socket.timeout as exc:
            raise FetchError("网络请求超时") from exc

        try:
            return raw.decode(charset)
        except UnicodeDecodeError:
            return raw.decode("utf-8", errors="replace")

