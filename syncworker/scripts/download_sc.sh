#!/bin/bash
source "$(dirname "$0")/config.sh"

LOG_FILE="/tmp/yt-dlp-last.log"

echo "--- Шаг 1: Загрузка новых треков из SoundCloud ---"
yt-dlp -i --download-archive "$ARCHIVE_FILE" \
  --format "bestaudio/best" --extract-audio --audio-quality 0 \
  --embed-metadata --embed-thumbnail \
  --output "$MUSIC_DIR/[%(id)s] %(title)s.%(ext)s" \
  "$SOUNDCLOUD_URL" 2>&1 | tee "$LOG_FILE"

  rc=${PIPESTATUS[0]}

echo "--- yt-dlp exit code: $rc ---"

if [ "$rc" -ne 0 ]; then
  echo "⚠️ yt-dlp завершился с ошибкой. Последние подозрительные строки:"
  grep -Ei "ERROR|unavailable|not available|region|country|forbidden|denied|failed|private" "$LOG_FILE" || true
fi

exit "$rc"