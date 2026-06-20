from __future__ import annotations

from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL  # type: ignore[import-untyped]

from syncworker.adapters.models.soundcloud_models import (
    SoundCloudDownloadResult,
    SoundCloudLibrary,
    SoundCloudPlaylist,
    SoundCloudTrack,
)


class SoundCloudAdapter:
    def __init__(self, url: str):
        self.url = url

    def download_tracks(self, music_dir: Path, archive_file: Path) -> SoundCloudDownloadResult:
        music_dir.mkdir(parents=True, exist_ok=True)
        archive_file.parent.mkdir(parents=True, exist_ok=True)

        options = {
            "ignoreerrors": True,
            "download_archive": str(archive_file),
            "format": "bestaudio/best",
            "outtmpl": str(music_dir / "[%(id)s] %(title)s.%(ext)s"),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredquality": "0",
                },
                {"key": "FFmpegMetadata"},
                {"key": "EmbedThumbnail"},
            ],
            "writethumbnail": True,
        }

        with YoutubeDL(options) as ydl:
            exit_code = ydl.download([self.url])

        return SoundCloudDownloadResult(exit_code=exit_code)

    def get_library(self) -> SoundCloudLibrary:
        root = self._extract_flat(self.url)
        entries = self._entries(root)

        liked_tracks: list[SoundCloudTrack] = []
        playlists: list[SoundCloudPlaylist] = []

        for entry in entries:
            item_id = self._required_str(entry, "id")
            title = self._required_str(entry, "title")
            url = self._required_str(entry, "url")

            if self._is_playlist(url):
                playlists.append(
                    SoundCloudPlaylist(
                        id=item_id,
                        url=url,
                        title=title,
                        tracks=self._get_playlist_tracks(url),
                    )
                )
                continue

            liked_tracks.append(SoundCloudTrack(id=item_id, url=url, title=title))

        return SoundCloudLibrary(liked_tracks=tuple(liked_tracks), playlists=tuple(playlists))

    def _get_playlist_tracks(self, playlist_url: str) -> tuple[SoundCloudTrack, ...]:
        playlist = self._extract_flat(playlist_url)
        return tuple(
            SoundCloudTrack(
                id=self._required_str(entry, "id"),
                url=self._required_str(entry, "url"),
                title=self._required_str(entry, "title"),
            )
            for entry in self._entries(playlist)
            if entry.get("id") is not None and entry.get("url") is not None and entry.get("title") is not None
        )

    @staticmethod
    def _extract_flat(url: str) -> dict[str, Any]:
        with YoutubeDL({"extract_flat": True, "quiet": True, "no_warnings": True}) as ydl:
            result = ydl.extract_info(url, download=False)

        if not isinstance(result, dict):
            raise RuntimeError(f"Invalid SoundCloud response for url: {url}")

        return result

    @staticmethod
    def _entries(result: dict[str, Any]) -> tuple[dict[str, Any], ...]:
        entries = result.get("entries") or []
        if not isinstance(entries, list):
            return ()

        return tuple(entry for entry in entries if isinstance(entry, dict))

    @staticmethod
    def _is_playlist(url: str) -> bool:
        return "/sets/" in url

    @staticmethod
    def _required_str(entry: dict[str, Any], field: str) -> str:
        value = entry.get(field)
        if value is None:
            raise RuntimeError(f"SoundCloud entry has no {field}: {entry}")

        return str(value)
