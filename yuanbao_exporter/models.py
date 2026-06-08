from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TranscriptLine:
    speaker: str
    timestamp: str
    text: str


@dataclass(frozen=True)
class RecordingExport:
    url: str
    title: str
    summary: str
    transcript: list[TranscriptLine]

