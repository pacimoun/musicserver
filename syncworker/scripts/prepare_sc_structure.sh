#!/bin/bash
set -e
source "$(dirname "$0")/config.sh"

SNAPSHOT_DIR=$1
LIKES_FILE="$SNAPSHOT_DIR/likes.json"
ENTRIES_FILE="$SNAPSHOT_DIR/entries.jsonl"
IDS_FILE="$SNAPSHOT_DIR/track_ids.unsorted"
> "$IDS_FILE"

read_playlist() {
    yt-dlp --flat-playlist --dump-single-json "$1" > "$2" &&
        jq -e '.entries | type == "array" and all(.[];
            (.id | type == "string" and test("^[0-9]+$")) and
            (.url | type == "string" and length > 0)
        )' "$2" > /dev/null
}

if ! read_playlist "$SOUNDCLOUD_URL" "$LIKES_FILE" ||
   ! jq -c '.entries | reverse | .[]' "$LIKES_FILE" > "$ENTRIES_FILE"; then
    echo "Не удалось прочитать список лайков SoundCloud" >&2
    exit 1
fi

# Fetch all sets before using their IDs to remove files from the library.
while IFS= read -r entry; do
    item_url=$(jq -r '.url' <<< "$entry")
    id=$(jq -r '.id' <<< "$entry")

    if [[ "$item_url" == *"/sets/"* ]]; then
        if ! read_playlist "$item_url" "$SNAPSHOT_DIR/set-$id.json" ||
           ! jq -r '.entries[].id' "$SNAPSHOT_DIR/set-$id.json" > "$SNAPSHOT_DIR/set-$id.ids"; then
            echo "Не удалось прочитать плейлист SoundCloud $id" >&2
            exit 1
        fi
        cat "$SNAPSHOT_DIR/set-$id.ids" >> "$IDS_FILE"
    else
        printf '%s\n' "$id" >> "$IDS_FILE"
    fi
done < "$ENTRIES_FILE"

sort -u "$IDS_FILE" > "$SNAPSHOT_DIR/track_ids"
