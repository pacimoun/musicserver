from __future__ import annotations

from syncworker.adapters.filesystem_adapter import FilesystemAdapter
from syncworker.adapters.navidrome_adapter import NavidromeAdapter
from syncworker.adapters.soundcloud_adapter import SoundCloudAdapter
from syncworker.config import Config
from syncworker.repository.library_repository import LibraryRepository
from syncworker.services.full_sync_service import FullSyncService
from syncworker.usecases.clear_navidrome_likes_usecase import ClearNavidromeLikesUseCase
from syncworker.usecases.download_soundcloud_tracks_usecase import DownloadSoundCloudTracksUseCase
from syncworker.usecases.remove_unliked_tracks_usecase import RemoveUnlikedTracksUseCase
from syncworker.usecases.scan_navidrome_usecase import ScanNavidromeUseCase
from syncworker.usecases.sync_liked_tracks_usecase import SyncLikedTracksUseCase
from syncworker.usecases.sync_playlists_usecase import SyncPlaylistsUseCase


def create_full_sync_service(config: Config) -> FullSyncService:
    soundcloud_adapter = SoundCloudAdapter(config.soundcloud_url)
    navidrome_adapter = NavidromeAdapter(
        base_url=config.navidrome_base_url,
        user=config.navidrome_user,
        password=config.navidrome_password,
    )
    filesystem_adapter = FilesystemAdapter(
        music_dir=config.music_dir,
        playlists_dir=config.playlists_dir,
        archive_file=config.archive_file,
    )

    clear_likes_usecase = ClearNavidromeLikesUseCase(navidrome_adapter)

    return FullSyncService(
        download_soundcloud_tracks_usecase=DownloadSoundCloudTracksUseCase(
            soundcloud_adapter=soundcloud_adapter,
            music_dir=config.music_dir,
            archive_file=config.archive_file,
        ),
        scan_navidrome_usecase=ScanNavidromeUseCase(navidrome_adapter),
        library_repository=LibraryRepository(
            soundcloud_adapter=soundcloud_adapter,
            navidrome_adapter=navidrome_adapter,
        ),
        remove_unliked_tracks_usecase=RemoveUnlikedTracksUseCase(filesystem_adapter),
        sync_liked_tracks_usecase=SyncLikedTracksUseCase(
            navidrome_adapter=navidrome_adapter,
            clear_likes_usecase=clear_likes_usecase,
        ),
        sync_playlists_usecase=SyncPlaylistsUseCase(filesystem_adapter),
    )
