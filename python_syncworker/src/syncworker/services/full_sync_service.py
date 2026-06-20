from __future__ import annotations

from syncworker.repository.library_repository import LibraryRepository
from syncworker.usecases.download_soundcloud_tracks_usecase import DownloadSoundCloudTracksUseCase
from syncworker.usecases.remove_unliked_tracks_usecase import RemoveUnlikedTracksUseCase
from syncworker.usecases.scan_navidrome_usecase import ScanNavidromeUseCase
from syncworker.usecases.sync_liked_tracks_usecase import SyncLikedTracksUseCase
from syncworker.usecases.sync_playlists_usecase import SyncPlaylistsUseCase


class FullSyncService:
    def __init__(
        self,
        download_soundcloud_tracks_usecase: DownloadSoundCloudTracksUseCase,
        scan_navidrome_usecase: ScanNavidromeUseCase,
        library_repository: LibraryRepository,
        remove_unliked_tracks_usecase: RemoveUnlikedTracksUseCase,
        sync_liked_tracks_usecase: SyncLikedTracksUseCase,
        sync_playlists_usecase: SyncPlaylistsUseCase,
    ):
        self.download_soundcloud_tracks_usecase = download_soundcloud_tracks_usecase
        self.scan_navidrome_usecase = scan_navidrome_usecase
        self.library_repository = library_repository
        self.remove_unliked_tracks_usecase = remove_unliked_tracks_usecase
        self.sync_liked_tracks_usecase = sync_liked_tracks_usecase
        self.sync_playlists_usecase = sync_playlists_usecase

    def run(self) -> None:
        self.download_soundcloud_tracks_usecase.execute()

        self.scan_navidrome_usecase.execute()

        library = self.library_repository.get_library()
        self.remove_unliked_tracks_usecase.execute(library)

        self.scan_navidrome_usecase.execute()

        self.sync_liked_tracks_usecase.execute(library)
        self.sync_playlists_usecase.execute(library)

        self.scan_navidrome_usecase.execute()
