#!/bin/bash
source "$(dirname "$0")/config.sh"

echo "--- Шаг 1: Загрузка новых треков из SoundCloud ---"
yt-dlp -v -i --download-archive "$ARCHIVE_FILE" \
  --format "bestaudio/best" --extract-audio --audio-quality 0 \
  --embed-metadata --embed-thumbnail \
  --output "$MUSIC_DIR/[%(id)s] %(title)s.%(ext)s" \
  "$SOUNDCLOUD_URL"