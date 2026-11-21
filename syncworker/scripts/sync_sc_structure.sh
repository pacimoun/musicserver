#!/bin/bash
source "$(dirname "$0")/config.sh"

echo "--- Шаг 3: Синхронизация лайков и создание плейлистов ---"

SNAPSHOT_DIR=${1:-}
if [[ -z "$SNAPSHOT_DIR" ]]; then
    SNAPSHOT_DIR=$(mktemp -d) || exit 1
    trap 'rm -r -- "$SNAPSHOT_DIR"' EXIT
    "$(dirname "$0")/prepare_sc_structure.sh" "$SNAPSHOT_DIR" || exit 1
fi
ENTRIES_FILE="$SNAPSHOT_DIR/entries.jsonl"
VALID_IDS_FILE="$SNAPSHOT_DIR/track_ids"
if [[ ! -r "$ENTRIES_FILE" || ! -r "$VALID_IDS_FILE" ]]; then
    echo "Список лайков SoundCloud не подготовлен" >&2
    exit 1
fi

declare -A LOCAL_TRACKS
for file in "$MUSIC_DIR"/*; do
    filename=${file##*/}
    if [[ -f "$file" && "$filename" =~ ^\[([0-9]+)\]\  ]]; then
        case "$filename" in
            *.part|*.part-Frag*|*.ytdl) continue ;;
        esac
        LOCAL_TRACKS[${BASH_REMATCH[1]}]="$filename"
    fi
done

echo "Очистка старых лайков в Navidrome"

STARRED_RESULT=$(curl -s "$ENDPOINT_GET_STARRED")

mapfile -t STARRED_IDS < <(
    echo "$STARRED_RESULT" | jq -r '
        .["subsonic-response"].starred
        | .song[]?.id,
          .album[]?.id,
          .artist[]?.id
        // empty
    '
)

if [ "${#STARRED_IDS[@]}" -gt 0 ]; then
    UNSTAR_QUERY=""
    for STARRED_ID in "${STARRED_IDS[@]}"; do
        UNSTAR_QUERY="${UNSTAR_QUERY}&id=$(printf '%s' "$STARRED_ID" | jq -sRr @uri)"
    done

    curl -s "${ENDPOINT_UNSTAR}${UNSTAR_QUERY}" > /dev/null
    echo " 🧹 -> Удалено старых лайков: ${#STARRED_IDS[@]}"
else
    echo " 🧹 -> Старых лайков не найдено"
fi

echo "Добавление новых лайков"

rm -f "$PLAYLISTS_DIR"/*.m3u

while IFS= read -r entry; do
    item_url=$(jq -r '.url' <<< "$entry")
    id=$(jq -r '.id' <<< "$entry")
    raw_title=$(jq -r '.title' <<< "$entry")
    clean_title=$(echo "$raw_title" | tr -d '/\?%*:|"<>' | sed 's/^[.-]*//')
    [ -z "$clean_title" ] && clean_title="unnamed_playlist_${id}"

    if [[ "$item_url" == *"/sets/"* ]]; then
        echo "[Playlist] Создаем: $raw_title"
        M3U_FILE="$PLAYLISTS_DIR/$clean_title.m3u"
        echo "#EXTM3U" > "$M3U_FILE"

        while IFS= read -r track_id; do
            filename=${LOCAL_TRACKS[$track_id]}
            [ -n "$filename" ] && printf '../%s\n' "$filename" >> "$M3U_FILE"
        done < "$SNAPSHOT_DIR/set-$id.ids"
    else
        echo "[Like] Обработка трека: $raw_title"

        filename=${LOCAL_TRACKS[$id]}
        if [[ -z "$filename" ]]; then
            echo " ❌ -> Трек не найден в библиотеке"
            continue
        fi
        file_size=$(stat -c %s -- "$MUSIC_DIR/$filename")
        SEARCH_QUERY=$(printf '%s' "$raw_title" | jq -sRr @uri)
        SEARCH_RESULT=$(curl -fsS "${ENDPOINT_SEARCH}&query=${SEARCH_QUERY}&songCount=100")

        TRACK_ID=$(echo "$SEARCH_RESULT" | jq -r \
            --arg title "$raw_title" --argjson size "$file_size" '
            [."subsonic-response".searchResult3.song[]? | select(.title == $title)] as $same_title
            | [$same_title[] | select(.size == $size)] as $same_file
            | if ($same_file | length) == 1 then $same_file[0].id
              elif ($same_title | length) == 1 then $same_title[0].id
              else empty
              end
            ')

        if [ -n "$TRACK_ID" ] && [ "$TRACK_ID" != "null" ]; then
            curl -s "${ENDPOINT_STAR}&id=${TRACK_ID}" > /dev/null
            echo " ✅ -> Лайк поставлен в Navidrome"
        else
            echo " ❌ -> Трек не найден в библиотеке"
        fi
    fi
done < "$ENTRIES_FILE"

echo "Очистка удаленных лайков"

for file in "$MUSIC_DIR"/*\[*\].*; do
    filename=${file##*/}
    if [[ ! -f "$file" || ! "$filename" =~ ^\[([0-9]+)\]\  ]]; then
        continue
    fi
    track_id=${BASH_REMATCH[1]}

    if ! grep -Fxq "$track_id" "$VALID_IDS_FILE"; then
        echo "Удаляем: $file"
        rm -f "$file"
        sed -i "/^soundcloud $track_id$/d" "$ARCHIVE_FILE"
    fi
done
