"""Find alternate SoundCloud uploads of the same recording."""

from collections.abc import Iterable
import json
import re
import unicodedata


FEATURE_CREDIT = re.compile(r'\s+(?:\(\s*)?(?:feat(?:uring)?\.?|ft\.?|w/)\s+', re.IGNORECASE)
ARTIST_PREFIX = re.compile(r'\s+[-–—]\s+')
ALTERNATE_VERSION = re.compile(
    r'\b(?:cover|кавер\w*|ремикс\w*|remix|instrumental|minus one|караоке|'
    r'sped up|speed up|slowed|nightcore|live version|bootleg)\b', re.IGNORECASE,
)


def normalize(value):
    value = unicodedata.normalize('NFKC', value).casefold().replace('ё', 'е')
    return ' '.join(re.findall(r'[^\W_]+', value))


def names(artists):
    return {normalize(name) for artist in artists
            for name in re.split(r'[,;&·]', artist) if normalize(name)}


def recording_title(title, artists):
    prefix = ARTIST_PREFIX.split(title, maxsplit=1)
    if len(prefix) == 2 and normalize(prefix[0]) in artists:
        title = prefix[1]
    parts = FEATURE_CREDIT.split(title, maxsplit=1)
    guests = names(parts[1:])
    return normalize(parts[0]), guests


def find_candidates(track, artist, trusted_artists, yt_dlp) -> Iterable[str]:
    title = track['title']
    duration = track['duration']
    expected_title, expected_guests = recording_title(title, trusted_artists)
    expected_credits = trusted_artists | expected_guests
    query = f'scsearch12:{artist} {title}'
    entries = json.loads(yt_dlp('--flat-playlist', '--dump-single-json', '--', query)).get('entries') or []
    matches = []

    for entry in entries:
        if not entry:
            continue
        candidate_id = str(entry.get('id', ''))
        if candidate_id == str(track['id']) or not re.fullmatch(r'[0-9]+', candidate_id):
            continue
        candidate_duration = entry.get('duration')
        if not isinstance(candidate_duration, (float, int)) or candidate_duration <= 0:
            continue
        difference = abs(duration - candidate_duration)
        candidate_title, candidate_guests = recording_title(entry.get('title') or '', trusted_artists)
        if candidate_title != expected_title or candidate_guests != expected_guests:
            continue
        if ALTERNATE_VERSION.search(entry.get('description') or '') and not ALTERNATE_VERSION.search(title):
            continue

        candidate_credits = names(entry.get('artists') or []) | candidate_guests
        same_uploader = track.get('uploader_id') and track['uploader_id'] == entry.get('uploader_id')
        # Require a precise duration and matching credits from a different uploader.
        if (same_uploader and difference <= min(3, duration * 0.02)
                or candidate_credits == expected_credits and difference <= 0.03):
            matches.append((difference, candidate_id))

    yield from dict.fromkeys(candidate_id for _, candidate_id in sorted(matches))
