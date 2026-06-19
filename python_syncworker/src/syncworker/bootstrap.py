from __future__ import annotations

import logging

from syncworker.config import Config

logger = logging.getLogger(__name__)


FAVORITES_NSP = """{
  "all": [
    {"is": {"loved": true}}
  ],
  "sort": "dateLoved",
  "order": "desc"
}
"""


def bootstrap(config: Config) -> None:
    config.playlists_dir.mkdir(parents=True, exist_ok=True)

    favorites_file = config.playlists_dir / "favorites.nsp"

    if favorites_file.exists():
        logger.info("Smart playlist already exists: %s", favorites_file)
        return

    favorites_file.write_text(FAVORITES_NSP, encoding="utf-8")
    favorites_file.chmod(0o644)

    logger.info("Smart playlist created: %s", favorites_file)