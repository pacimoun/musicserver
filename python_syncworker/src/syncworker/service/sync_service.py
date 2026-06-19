from __future__ import annotations

import logging

from syncworker.config import Config

logger = logging.getLogger(__name__)

class SyncService:
    config: Config

    def __init__(self, config: Config):
        self.config = config

    def run_full_sync(self):
        logger.info("Full sync started")
        return