from __future__ import annotations

import time

from syncworker.adapters.navidrome_adapter import NavidromeAdapter


class ScanNavidromeUseCase:
    def __init__(
        self,
        navidrome_adapter: NavidromeAdapter,
        poll_interval_seconds: float = 1,
    ):
        self.navidrome_adapter = navidrome_adapter
        self.poll_interval_seconds = poll_interval_seconds

    def execute(self) -> None:
        self.navidrome_adapter.start_scan()

        while self.navidrome_adapter.get_scan_status().scanning:
            time.sleep(self.poll_interval_seconds)
