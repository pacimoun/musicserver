from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NavidromeSong:
    id: str
    title: str
    soundcloud_id: str
    path: str
    artist: str | None = None
    album: str | None = None


@dataclass(frozen=True)
class ScanStatus:
    scanning: bool
    count: int | None = None


@dataclass(frozen=True)
class StarredItems:
    song_ids: tuple[str, ...]
    album_ids: tuple[str, ...]
    artist_ids: tuple[str, ...]

    @property
    def all_ids(self) -> tuple[str, ...]:
        return self.song_ids + self.album_ids + self.artist_ids
