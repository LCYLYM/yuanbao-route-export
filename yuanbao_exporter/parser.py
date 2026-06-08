from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from typing import Any

from .models import RecordingExport, TranscriptLine


class ParseError(RuntimeError):
    pass


class _NextDataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._capturing = False
        self._chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "script":
            return
        attr_map = {key: value for key, value in attrs}
        if attr_map.get("id") == "__NEXT_DATA__":
            self._capturing = True

    def handle_data(self, data: str) -> None:
        if self._capturing:
            self._chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._capturing:
            self._capturing = False

    @property
    def data(self) -> str:
        return "".join(self._chunks).strip()


def parse_yuanbao_page(*, url: str, html_text: str) -> RecordingExport:
    next_data = _extract_next_data(html_text)
    page_props = _get_path(next_data, ["props", "pageProps"])
    if not isinstance(page_props, dict):
        raise ParseError("页面数据结构异常：缺少 pageProps。")

    if page_props.get("isShareDel"):
        raise ParseError("该分享已被删除或不可访问。")

    title = _read_title(page_props)
    summary = _read_summary(page_props)
    role_map = _read_role_map(page_props)
    transcript = _read_transcript(page_props, role_map)
    if not transcript:
        raise ParseError("未解析到实时转写内容。")

    return RecordingExport(
        url=url,
        title=title,
        summary=summary,
        transcript=transcript,
    )


def _extract_next_data(html_text: str) -> dict[str, Any]:
    parser = _NextDataParser()
    parser.feed(html_text)
    raw = parser.data
    if not raw:
        raise ParseError("未找到 __NEXT_DATA__，页面结构可能已变化或需要验证。")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ParseError(f"__NEXT_DATA__ JSON 解析失败：{exc}") from exc
    if not isinstance(parsed, dict):
        raise ParseError("__NEXT_DATA__ 顶层结构异常。")
    return parsed


def _get_path(data: dict[str, Any], path: list[str]) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _read_title(page_props: dict[str, Any]) -> str:
    voice_summary = page_props.get("voiceSummary")
    if isinstance(voice_summary, dict) and voice_summary.get("title"):
        return str(voice_summary["title"]).strip()

    recorder = page_props.get("recorder")
    if isinstance(recorder, dict) and recorder.get("title"):
        return str(recorder["title"]).strip()
    return "未命名录音"


def _read_summary(page_props: dict[str, Any]) -> str:
    voice_summary = page_props.get("voiceSummary")
    if not isinstance(voice_summary, dict):
        return ""
    summary = voice_summary.get("summary")
    return _clean_text(str(summary)) if summary else ""


def _read_role_map(page_props: dict[str, Any]) -> dict[str, str]:
    role_infos = page_props.get("voiceIdRoleInfos")
    role_map: dict[str, str] = {}
    if not isinstance(role_infos, list):
        return role_map

    for info in role_infos:
        if not isinstance(info, dict):
            continue
        voice_id = info.get("voiceId")
        nickname = info.get("nickname")
        if voice_id is None or not nickname:
            continue
        role_map[str(voice_id)] = _clean_text(str(nickname))
    return role_map


def _read_transcript(
    page_props: dict[str, Any],
    role_map: dict[str, str],
) -> list[TranscriptLine]:
    sentences = page_props.get("voiceSentences")
    if not isinstance(sentences, list):
        return []

    transcript: list[TranscriptLine] = []
    sorted_sentences = sorted(
        (item for item in sentences if isinstance(item, dict)),
        key=lambda item: _safe_int(item.get("startTime")),
    )

    for item in sorted_sentences:
        text = _clean_text(str(item.get("sourceText") or ""))
        if not text:
            continue
        voice_id = str(item.get("voiceId", ""))
        speaker = role_map.get(voice_id) or _fallback_speaker(voice_id)
        transcript.append(
            TranscriptLine(
                speaker=speaker,
                timestamp=format_timestamp(_safe_int(item.get("startTime"))),
                text=text,
            )
        )
    return transcript


def _fallback_speaker(voice_id: str) -> str:
    return f"说话人{voice_id}" if voice_id else "未知说话人"


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def format_timestamp(milliseconds: int) -> str:
    total_seconds = max(0, milliseconds // 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def _clean_text(value: str) -> str:
    value = value.replace("\x00", "")
    value = re.sub(r"[ \t\r\f\v]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()

