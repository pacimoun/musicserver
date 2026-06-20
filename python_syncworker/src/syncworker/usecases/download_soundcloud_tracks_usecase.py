from __future__ import annotations

from pathlib import Path

from syncworker.adapters.models.soundcloud_models import SoundCloudDownloadResult
from syncworker.adapters.soundcloud_adapter import SoundCloudAdapter


class DownloadSoundCloudTracksUseCase:
    def __init__(
        self,
        soundcloud_adapter: SoundCloudAdapter,
        music_dir: Path,
        archive_file: Path,
    ):
        self.soundcloud_adapter = soundcloud_adapter
        self.music_dir = music_dir
        self.archive_file = archive_file

    def execute(self) -> SoundCloudDownloadResult:
        return self.soundcloud_adapter.download_tracks(
            music_dir=self.music_dir,
            archive_file=self.archive_file,
        )
