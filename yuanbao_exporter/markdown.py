from __future__ import annotations

from datetime import datetime

from .models import RecordingExport


def render_markdown(recordings: list[RecordingExport], *, mode: str) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: list[str] = [
        "# 元宝录音导出",
        "",
        f"导出时间：{generated_at}",
        f"导出方式：{'带人物' if mode == 'with-speakers' else '纯文字'}",
        "",
    ]

    for index, recording in enumerate(recordings, start=1):
        title = recording.title or f"录音 {index}"
        _append_recording(lines, recording, mode=mode, heading=f"## {index}. {title}")

    return "\n".join(lines).rstrip() + "\n"


def render_single_markdown(recording: RecordingExport, *, mode: str) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = recording.title or "未命名录音"
    lines: list[str] = [
        f"# {title}",
        "",
        f"导出时间：{generated_at}",
        f"导出方式：{'带人物' if mode == 'with-speakers' else '纯文字'}",
        "",
    ]
    _append_recording(lines, recording, mode=mode, heading=None)
    return "\n".join(lines).rstrip() + "\n"


def _append_recording(
    lines: list[str],
    recording: RecordingExport,
    *,
    mode: str,
    heading: str | None,
) -> None:
    if heading:
        lines.extend([heading, ""])

    lines.extend([f"来源：{recording.url}", ""])

    if recording.summary:
        lines.extend(["### AI 总结", "", recording.summary.strip(), ""])

    lines.extend(["### 实时转写", ""])
    if mode == "with-speakers":
        lines.extend(_render_transcript_with_speakers(recording))
    else:
        lines.extend(_render_transcript_plain(recording))
    lines.append("")


def _render_transcript_with_speakers(recording: RecordingExport) -> list[str]:
    lines: list[str] = []
    for item in recording.transcript:
        speaker = item.speaker or "未知说话人"
        timestamp = item.timestamp or "00:00"
        lines.extend([f"{speaker} {timestamp}", item.text, ""])
    return lines


def _render_transcript_plain(recording: RecordingExport) -> list[str]:
    return [item.text for item in recording.transcript]
