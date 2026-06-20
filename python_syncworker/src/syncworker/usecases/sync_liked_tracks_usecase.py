from __future__ import annotations

from syncworker.adapters.navidrome_adapter import NavidromeAdapter
from syncworker.models.library_models import MusicLibrary
from syncworker.usecases.clear_navidrome_likes_usecase import ClearNavidromeLikesUseCase


class SyncLikedTracksUseCase:
    def __init__(
        self,
        navidrome_adapter: NavidromeAdapter,
        clear_likes_usecase: ClearNavidromeLikesUseCase,
    ):
        self.navidrome_adapter = navidrome_adapter
        self.clear_likes_usecase = clear_likes_usecase

    def execute(self, library: MusicLibrary) -> None:
        self.clear_likes_usecase.execute()

        for track in library.liked_tracks:
            self.navidrome_adapter.star(track.navidrome_id)
