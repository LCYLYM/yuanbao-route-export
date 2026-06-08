from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from urllib.parse import urlparse

from .fetcher import FetchError, YuanbaoClient
from .link_extractor import LinkExtractionError, extract_yuanbao_links
from .markdown import render_markdown, render_single_markdown
from .parser import ParseError, parse_yuanbao_page


LOGGER = logging.getLogger(__name__)
SUPPORTED_MODES = {"with-speakers", "plain-text"}


class ExportError(RuntimeError):
    pass


@dataclass(frozen=True)
class FetchJob:
    index: int
    url: str


@dataclass(frozen=True)
class MarkdownDocument:
    filename: str
    content: str


def build_markdown_from_input(
    *,
    raw_input: str,
    mode: str,
    proxy_url: str | None = None,
) -> str:
    recordings = fetch_recordings_from_input(
        raw_input=raw_input,
        mode=mode,
        proxy_url=proxy_url,
    )
    return render_markdown(recordings, mode=mode)


def build_markdown_documents_from_input(
    *,
    raw_input: str,
    mode: str,
    proxy_url: str | None = None,
) -> list[MarkdownDocument]:
    recordings = fetch_recordings_from_input(
        raw_input=raw_input,
        mode=mode,
        proxy_url=proxy_url,
    )
    return [
        MarkdownDocument(
            filename=_build_document_filename(index, recording),
            content=render_single_markdown(recording, mode=mode),
        )
        for index, recording in enumerate(recordings, start=1)
    ]


def fetch_recordings_from_input(
    *,
    raw_input: str,
    mode: str,
    proxy_url: str | None = None,
):
    if mode not in SUPPORTED_MODES:
        raise ExportError(f"不支持的导出方式：{mode}")

    try:
        urls = extract_yuanbao_links(raw_input)
    except LinkExtractionError as exc:
        raise ExportError(str(exc)) from exc

    client = YuanbaoClient(proxy_url=proxy_url)
    recordings = [None] * len(urls)
    jobs = [FetchJob(index=index, url=url) for index, url in enumerate(urls)]
    max_workers = min(4, len(jobs))

    LOGGER.info("exporting %s yuanbao share(s)", len(jobs))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_fetch_and_parse, client, job.url): job
            for job in jobs
        }
        for future in as_completed(futures):
            job = futures[future]
            try:
                recordings[job.index] = future.result()
            except (FetchError, ParseError) as exc:
                raise ExportError(f"{job.url} 处理失败：{exc}") from exc

    parsed_recordings = [recording for recording in recordings if recording is not None]
    if not parsed_recordings:
        raise ExportError("没有可导出的录音内容。")
    return parsed_recordings


def _fetch_and_parse(client: YuanbaoClient, url: str):
    html = client.fetch_html(url)
    return parse_yuanbao_page(url=url, html_text=html)


def _build_document_filename(index: int, recording) -> str:
    share_id = _share_id_from_url(recording.url)
    title = _safe_filename_part(recording.title) or "yuanbao-recording"
    suffix = share_id[:8] if share_id else f"{index:02d}"
    return f"{index:02d}-{title}-{suffix}.md"[:180]


def _share_id_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1] if path else ""


def _safe_filename_part(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|\x00-\x1f]+", " ", value)
    value = re.sub(r"\s+", "-", value.strip())
    value = re.sub(r"-{2,}", "-", value)
    return value.strip(".-")
