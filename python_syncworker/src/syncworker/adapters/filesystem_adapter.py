from __future__ import annotations

import fileinput
import re
import sys
from pathlib import Path

from syncworker.adapters.models.filesystem_models import ArchiveEntry, LocalTrack

SOUNDCLOUD_ID_PATTERN = re.compile(r"\[(?P<id>\d+)]")
INVALID_PLAYLIST_FILENAME_CHARS = str.maketrans("", "", '/\\?%*:|"<>')

class FilesystemAdapter:
    def __init__(self, music_dir: Path, playlists_dir: Path, archive_file: Path):
        self.music_dir = music_dir
        self.playlists_dir = playlists_dir
        self.archive_file = archive_file

    def list_tracks(self) -> tuple[LocalTrack, ...]:
        tracks: list[LocalTrack] = []

        if not self.music_dir.exists():
            return ()

        for path in self.music_dir.iterdir():
            if not path.is_file():
                continue

            track_id = self._extract_soundcloud_id(path.name)
            if track_id is None:
                continue

            tracks.append(LocalTrack(soundcloud_id=track_id, path=path))

        return tuple(sorted(tracks, key=lambda track: track.path.name))

    def find_track_by_soundcloud_id(self, soundcloud_id: str) -> LocalTrack | None:
        for track in self.list_tracks():
            if track.soundcloud_id == soundcloud_id:
                return track

        return None

    def read_archive(self) -> tuple[ArchiveEntry, ...]:
        if not self.archive_file.exists():
            return ()

        entries: list[ArchiveEntry] = []
        for raw_line in self.archive_file.read_text(encoding="utf-8").splitlines():
            entry = self._parse_archive_line(raw_line)
            if entry is not None:
                entries.append(entry)

        return tuple(entries)

    def remove_archive_entries(self, item_ids: set[str]) -> None:
        if not item_ids or not self.archive_file.exists():
            return

        removable_ids = {entry.item_id for entry in self.read_archive() if entry.item_id in item_ids}
        if not removable_ids:
            return

        with fileinput.input(
            files=(str(self.archive_file),),
            inplace=True,
            encoding="utf-8",
            errors="surrogateescape",
        ) as archive:
            for raw_line in archive:
                entry = self._parse_archive_line(raw_line)
                if entry is not None and entry.item_id in removable_ids:
                    continue

                sys.stdout.write(raw_line)

    def delete_track(self, track: LocalTrack) -> None:
        track.path.unlink(missing_ok=True)

    def delete_m3u_playlists(self) -> None:
        if not self.playlists_dir.exists():
            return

        for path in self.playlists_dir.glob("*.m3u"):
            path.unlink()

    def write_m3u_playlist(self, title: str, tracks: tuple[LocalTrack, ...]) -> Path:
        self.playlists_dir.mkdir(parents=True, exist_ok=True)
        playlist_file = self.playlists_dir / f"{self.sanitize_playlist_filename(title)}.m3u"
        lines = ["#EXTM3U"]
        lines.extend(f"../{track.filename}" for track in tracks)
        playlist_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return playlist_file

    def existing_archive_entries(self) -> tuple[ArchiveEntry, ...]:
        local_ids = {track.soundcloud_id for track in self.list_tracks()}
        return tuple(entry for entry in self.read_archive() if entry.item_id in local_ids)

    @staticmethod
    def sanitize_playlist_filename(title: str) -> str:
        clean_title = title.translate(INVALID_PLAYLIST_FILENAME_CHARS).lstrip(".-").strip()
        return clean_title or "unnamed_playlist"

    @staticmethod
    def _extract_soundcloud_id(filename: str) -> str | None:
        match = SOUNDCLOUD_ID_PATTERN.search(filename)
        if match is None:
            return None

        return match.group("id")

    @staticmethod
    def _parse_archive_line(raw_line: str) -> ArchiveEntry | None:
        line = raw_line.strip()
        if not line:
            return None

        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            return None

        return ArchiveEntry(extractor=parts[0], item_id=parts[1], raw=line)
