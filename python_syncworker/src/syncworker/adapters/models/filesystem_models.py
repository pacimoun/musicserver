from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalTrack:
    soundcloud_id: str
    path: Path


@dataclass(frozen=True)
class ArchiveEntry:
    extractor: str
    item_id: str
    raw: str
