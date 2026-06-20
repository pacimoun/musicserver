from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    music_dir: Path
    playlists_dir: Path
    archive_file: Path

    navidrome_base_url: str
    navidrome_user: str
    navidrome_password: str

    soundcloud_url: str
    sync_schedule: str

    timezone: str

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            music_dir=Path(required_env("MUSIC_DIR")),
            playlists_dir=Path(required_env("PLAYLISTS_DIR")),
            archive_file=Path(required_env("ARCHIVE_FILE")),
            navidrome_base_url=required_env("ND_BASE_URL"),
            navidrome_user=required_env("ND_USER"),
            navidrome_password=required_env("ND_PASS"),
            soundcloud_url=required_env("SOUNDCLOUD_URL"),
            sync_schedule=required_env("SYNC_SCHEDULE"),
            timezone=required_env("TZ"),
        )


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value
