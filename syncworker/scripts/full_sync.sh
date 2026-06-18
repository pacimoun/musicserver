#!/bin/bash
set -e

BASE_DIR=$(dirname "$0")

echo "=== ЗАПУСК ПОЛНОЙ СИНХРОНИЗАЦИИ ==="

$BASE_DIR/sync_archive.sh

if "$BASE_DIR/download_sc.sh"; then
  echo "✅ download_sc завершился успешно"
else
  rc=$?
  echo "⚠️ download_sc завершился с кодом $rc. Вероятно, часть треков недоступна. Продолжаем сканирования."
fi

$BASE_DIR/scan_navidrome.sh
$BASE_DIR/sync_sc_structure.sh
$BASE_DIR/scan_navidrome.sh

echo "=== СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА ==="