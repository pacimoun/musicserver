from __future__ import annotations

from syncworker.adapters.filesystem_adapter import FilesystemAdapter
from syncworker.models.library_models import MusicLibrary


class RemoveUnlikedTracksUseCase:
    def __init__(self, filesystem_adapter: FilesystemAdapter):
        self.filesystem_adapter = filesystem_adapter

    def execute(self, library: MusicLibrary) -> None:
        actual_soundcloud_ids = {track.soundcloud_id for track in library.all_tracks}

        archive_entry_ids = {entry.item_id for entry in self.filesystem_adapter.read_archive()}
        self.filesystem_adapter.remove_archive_entries(archive_entry_ids - actual_soundcloud_ids)

        for track in self.filesystem_adapter.list_tracks():
            if track.soundcloud_id not in actual_soundcloud_ids:
                FilesystemAdapter.delete_track(track)