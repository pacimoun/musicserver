#!/bin/bash
set -e

BASE_DIR=$(dirname "$0")
source "$BASE_DIR/config.sh"

exec 9>/tmp/musicserver-sync.lock
if ! flock -n 9; then
  echo "Синхронизация уже запущена"
  exit 1
fi

snapshot=$(mktemp -d)
trap 'rm -r -- "$snapshot"' EXIT

echo "=== ЗАПУСК ПОЛНОЙ СИНХРОНИЗАЦИИ ==="

"$BASE_DIR/prepare_sc_structure.sh" "$snapshot"
"$BASE_DIR/sync_archive.sh"

if "$BASE_DIR/download_sc.sh"; then
  echo "✅ download_sc завершился успешно"
else
  rc=$?
  echo "⚠️ download_sc завершился с кодом $rc. Проверяем недостающие треки."
fi

python3 "$BASE_DIR/fallback_sc.py" "$snapshot/track_ids" "$MUSIC_DIR" "$ARCHIVE_FILE"
"$BASE_DIR/scan_navidrome.sh"
"$BASE_DIR/sync_sc_structure.sh" "$snapshot"
"$BASE_DIR/scan_navidrome.sh"

echo "=== СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА ==="
