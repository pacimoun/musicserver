from __future__ import annotations

import logging
from collections.abc import Callable

from apscheduler.schedulers.blocking import BlockingScheduler  # type: ignore[import-untyped]
from apscheduler.triggers.cron import CronTrigger  # type: ignore[import-untyped]

from syncworker.config import Config

logger = logging.getLogger(__name__)

def run_worker(config: Config, job: Callable[[], None]) -> None:
    scheduler = BlockingScheduler(
        timezone=config.timezone,
        job_defaults={
            "coalesce": True,
            "max_instances": 1,
        },
    )

    scheduler.add_job(
        job,
        trigger=CronTrigger.from_crontab(config.sync_schedule),
        id="full_sync",
        name="Full sync",
        replace_existing=True,
    )

    logger.info("worker started. schedule: %s", config.sync_schedule)

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker stopped")
