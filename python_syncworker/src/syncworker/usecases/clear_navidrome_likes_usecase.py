from __future__ import annotations

from syncworker.adapters.navidrome_adapter import NavidromeAdapter


class ClearNavidromeLikesUseCase:
    def __init__(self, navidrome_adapter: NavidromeAdapter):
        self.navidrome_adapter = navidrome_adapter

    def execute(self) -> None:
        starred = self.navidrome_adapter.get_starred()
        self.navidrome_adapter.unstar(starred.song_ids)
