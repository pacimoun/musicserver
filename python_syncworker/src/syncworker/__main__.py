from __future__ import annotations

import argparse
import logging
import sys

from syncworker.bootstrap import bootstrap
from syncworker.config import Config
from syncworker.scheduler import run_worker
from syncworker.service.sync_service import SyncService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="syncworker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("worker", help="Run scheduled sync worker")
    subparsers.add_parser("run-once", help="Run full sync once")
    subparsers.add_parser("bootstrap", help="Prepare directories and smart playlists")

    return parser


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    args = build_parser().parse_args()
    config = Config.from_env()

    if args.command == "bootstrap":
        bootstrap(config)
        return 0

    if args.command == "run-once":
        bootstrap(config)
        SyncService(config).run_full_sync()
        return 0

    if args.command == "worker":
        bootstrap(config)
        run_worker(config, lambda: SyncService(config).run_full_sync())
        return 0

    raise RuntimeError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    sys.exit(main())