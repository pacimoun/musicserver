#!/bin/bash
set -e

BASE_DIR=$(dirname "$0")

RUN_FIX=false

for arg in "$@"; do
  case $arg in
    -f|--fix-filenames)
      RUN_FIX=true
      shift
      ;;
  esac
done

echo "=== ЗАПУСК ПОЛНОЙ СИНХРОНИЗАЦИИ ==="

if [ "$RUN_FIX" = true ]; then
    echo "🛠️ Запуск фикса имен файлов"
    $BASE_DIR/fix_filenames.sh
else
    echo "ℹ️ Пропускаем фикс имен"
fi

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