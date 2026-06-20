from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SoundCloudTrack:
    id: str
    url: str
    title: str


@dataclass(frozen=True)
class SoundCloudPlaylist:
    id: str
    url: str
    title: str
    tracks: tuple[SoundCloudTrack, ...]


@dataclass(frozen=True)
class SoundCloudLibrary:
    liked_tracks: tuple[SoundCloudTrack, ...]
    playlists: tuple[SoundCloudPlaylist, ...]

    @property
    def all_tracks(self) -> tuple[SoundCloudTrack, ...]:
        tracks: list[SoundCloudTrack] = []
        tracks.extend(self.liked_tracks)

        for playlist in self.playlists:
            tracks.extend(playlist.tracks)

        return tuple(tracks)


@dataclass(frozen=True)
class SoundCloudDownloadResult:
    exit_code: int

    @property
    def success(self) -> bool:
        return self.exit_code == 0
