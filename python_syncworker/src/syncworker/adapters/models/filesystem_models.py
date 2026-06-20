from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalTrack:
    soundcloud_id: str
    path: Path

    @property
    def filename(self) -> str:
        return self.path.name


@dataclass(frozen=True)
class ArchiveEntry:
    extractor: str
    item_id: str
    raw: str
