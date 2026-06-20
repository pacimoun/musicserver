from __future__ import annotations

from syncworker.adapters.filesystem_adapter import FilesystemAdapter
from syncworker.models.library_models import MusicLibrary


class SyncPlaylistsUseCase:
    def __init__(self, filesystem_adapter: FilesystemAdapter):
        self.filesystem_adapter = filesystem_adapter

    def execute(self, library: MusicLibrary) -> None:
        self.filesystem_adapter.delete_m3u_playlists()

        for playlist in library.playlists:
            self.filesystem_adapter.write_m3u_playlist(
                title=playlist.title,
                track_paths=tuple(track.navidrome_path for track in playlist.tracks),
            )
