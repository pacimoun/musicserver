from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LibraryTrack:
    soundcloud_id: str
    navidrome_id: str
    soundcloud_url: str | None
    title: str
    navidrome_path: str

    @property
    def is_present_in_soundcloud(self) -> bool:
        return self.soundcloud_url is not None


@dataclass(frozen=True)
class LibraryPlaylist:
    soundcloud_id: str
    soundcloud_url: str
    title: str
    tracks: tuple[LibraryTrack, ...]


@dataclass(frozen=True)
class MusicLibrary:
    liked_tracks: tuple[LibraryTrack, ...]
    playlists: tuple[LibraryPlaylist, ...]

    @property
    def all_tracks(self) -> tuple[LibraryTrack, ...]:
        tracks: list[LibraryTrack] = []
        tracks.extend(self.liked_tracks)

        for playlist in self.playlists:
            tracks.extend(playlist.tracks)

        return tuple(tracks)
