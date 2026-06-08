from __future__ import annotations

import re
from urllib.parse import urlparse


YUANBAO_LINK_RE = re.compile(
    r"https?://yuanbao\.tencent\.com/e/rm/[0-9a-fA-F-]{32,36}(?:[/?#][^\s]*)?"
)


class LinkExtractionError(ValueError):
    pass


def extract_yuanbao_links(raw_input: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for match in YUANBAO_LINK_RE.finditer(raw_input):
        normalized = _normalize_url(match.group(0))
        if normalized not in seen:
            links.append(normalized)
            seen.add(normalized)

    if not links:
        raise LinkExtractionError("没有识别到元宝录音分享链接。")
    return links


def _normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise LinkExtractionError(f"不支持的链接协议：{parsed.scheme}")
    if parsed.netloc != "yuanbao.tencent.com":
        raise LinkExtractionError(f"不允许抓取该域名：{parsed.netloc}")
    if not parsed.path.startswith("/e/rm/"):
        raise LinkExtractionError(f"不是元宝录音分享链接：{url}")
    return parsed._replace(fragment="").geturl()

