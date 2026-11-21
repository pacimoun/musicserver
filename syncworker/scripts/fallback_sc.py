#!/usr/bin/env python3
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from itertools import product
import json
import math
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
import unicodedata

import bandcamp
import lmusic
import muzoi
import soundcloud_search
import zaycev


SOUNDCLOUD_FORMAT = 'download/bestaudio[format_id!$=_preview]/best[format_id!$=_preview]'
PRODUCER_CREDIT = re.compile(r'\s*(?:\(prod\.? by [^()]+\)|\[prod\.? by [^\[\]]+\])\s*$', re.IGNORECASE)
DOWNLOADERS = (
    ('Zaycev', zaycev.find_candidates),
    ('Bandcamp', bandcamp.find_candidates),
    ('Lmusic', lmusic.find_candidates),
    ('Muzoi', muzoi.find_candidates),
)


def command(args, timeout=90):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=True)
    return result.stdout


def yt_dlp(*args, timeout=65):
    return command([
        'yt-dlp', '--ignore-config', '--no-warnings', '--socket-timeout', '10',
        '--retries', '1', '--fragment-retries', '1', *args,
    ], timeout)


def normalize(value):
    value = unicodedata.normalize('NFKC', value).casefold().replace('ё', 'е')
    return ' '.join(re.findall(r'[^\W_]+', value))


def artist_names(values):
    credits = (
        normalize(artist)
        for value in values
        for group in soundcloud_search.FEATURE_CREDIT.split(value)
        for artist in re.split(r'[,;&·]', group)
    )
    return {artist for artist in credits if artist}


def same_duration(expected, actual):
    return abs(expected - actual) <= min(5, max(1.5, expected * 0.02))


def matches_track(title, candidate_artist, candidate_title, trusted_artists):
    artists = artist_names([candidate_artist])
    if not artists & trusted_artists:
        return False
    if normalize(title) == normalize(candidate_title):
        return True
    expected, guests = soundcloud_search.recording_title(PRODUCER_CREDIT.sub('', title), trusted_artists)
    candidate, candidate_guests = soundcloud_search.recording_title(
        PRODUCER_CREDIT.sub('', candidate_title), trusted_artists,
    )
    return (expected == candidate and guests <= (artists | candidate_guests)
            and candidate_guests <= (trusted_artists | guests))


def get_track(track_id):
    url = f'https://api.soundcloud.com/tracks/{track_id}'
    return json.loads(yt_dlp(
        '--ignore-no-formats-error', '--extractor-args', 'soundcloud:formats=none',
        '--dump-single-json', '--', url,
    ))


def inspect_audio(path):
    data = json.loads(command([
        'ffprobe', '-v', 'error', '-select_streams', 'a:0',
        '-show_entries', 'format=duration:format_tags=artist,title:stream=codec_name',
        '-of', 'json', str(path),
    ], timeout=20))
    info = data['format']
    return float(info['duration']), data['streams'][0]['codec_name'], info.get('tags', {})


def prepare_audio(path, destination, track, artist, source, local_artists=None):
    try:
        duration, codec, tags = inspect_audio(path)
    except (KeyError, ValueError, IndexError, subprocess.SubprocessError):
        return False
    if not same_duration(track['duration'], duration):
        return False
    if local_artists is not None:
        tags = {key.casefold(): value for key, value in tags.items()}
        if normalize(tags.get('title', '')) != normalize(track['title']):
            return False
        if not artist_names([tags.get('artist', '')]) & local_artists:
            return False
    command([
        'ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-y', '-i', str(path),
        '-map', '0:a:0', '-map_metadata', '-1', '-c:a', 'copy' if codec == 'mp3' else 'libmp3lame',
        '-metadata', f"title={track['title']}", '-metadata', f'artist={artist}',
        '-metadata', f"comment=SoundCloud ID {track['id']}; audio source: {source}",
        str(destination),
    ], timeout=90)
    return True


def save_track(track_id, music_dir, staging_dir, local_by_title):
    track = get_track(track_id)
    title = track.get('title')
    duration = track.get('duration')
    credited_artists = track.get('artists') or []
    uploader = track.get('uploader') or ''
    trusted_artists = artist_names(credited_artists or [uploader])
    if (not title or not isinstance(duration, (int, float)) or not math.isfinite(duration)
            or duration <= 0 or not trusted_artists):
        return None, 'нет метаданных для проверки версии'

    original_artist = ', '.join(dict.fromkeys(
        name.strip() for entry in (credited_artists or [uploader]) for name in entry.split(',') if name.strip()
    ))
    search_artists = {}
    for artist in (uploader, original_artist.split(',')[0], original_artist):
        key = normalize(artist)
        if key in trusted_artists or artist == original_artist:
            search_artists.setdefault(key, artist)
    search_artists = list(search_artists.values())
    directory = staging_dir / track_id
    directory.mkdir()
    incoming = directory / 'source'
    prepared = directory / 'track.mp3'
    filename_title = re.sub(r'[\\/\x00-\x1f]', '_', title).strip()
    filename_title = filename_title.encode()[:220].decode(errors='ignore')
    destination = music_dir / f'[{track_id}] {filename_title}.mp3'

    def publish(source, path, local_artists=None):
        if prepare_audio(path, prepared, track, original_artist, source, local_artists):
            prepared.replace(destination)
            return True
        return False

    expected_title = normalize(title)
    for path in local_by_title.get(expected_title, ()):
        try:
            if publish('локальная библиотека', path, trusted_artists):
                return 'локальная библиотека', title
        except subprocess.SubprocessError:
            continue

    base_title = soundcloud_search.FEATURE_CREDIT.split(PRODUCER_CREDIT.sub('', title), maxsplit=1)[0].strip()
    search_titles = dict.fromkeys((title, base_title))
    for source, find_candidates in DOWNLOADERS:
        seen = set()
        try:
            for query_title, artist in product(search_titles, search_artists):
                for url, candidate_artist, candidate_title in find_candidates(artist, query_title):
                    if url in seen or not matches_track(title, candidate_artist, candidate_title, trusted_artists):
                        continue
                    seen.add(url)
                    try:
                        command([
                            'curl', '--fail', '--silent', '--show-error', '--location', '--max-redirs', '2',
                            '--proto', '=https', '--proto-redir', '=https', '--connect-timeout', '10',
                            '--max-time', '90', '--speed-limit', '1024', '--speed-time', '15',
                            '--max-filesize', '100M', '--output', str(incoming), '--', url,
                        ], timeout=95)
                        if publish(source, incoming):
                            return source, title
                    except subprocess.SubprocessError:
                        continue
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            continue

    try:
        candidates = soundcloud_search.find_candidates(track, search_artists[0], trusted_artists, yt_dlp)
        for candidate_id in candidates:
            for old in directory.glob('mirror.*'):
                old.unlink()
            try:
                yt_dlp(
                    '--no-playlist', '--format', SOUNDCLOUD_FORMAT, '--extract-audio',
                    '--max-filesize', '100M', '--output', str(directory / 'mirror.%(ext)s'),
                    '--', f'https://api.soundcloud.com/tracks/{candidate_id}',
                )
                path = next(directory.glob('mirror.*'), None)
                if path and publish('SoundCloud', path):
                    return f'SoundCloud {candidate_id}', title
            except subprocess.SubprocessError:
                continue
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return None, title


def recover(track_id, music_dir, staging_dir, local_by_title):
    try:
        return save_track(track_id, music_dir, staging_dir, local_by_title)
    except (OSError, KeyError, ValueError, TypeError, AttributeError, subprocess.SubprocessError):
        return None, 'ошибка получения или сохранения аудио'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('track_ids', type=Path)
    parser.add_argument('music_dir', type=Path)
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    stored_ids = set()
    local_by_title = defaultdict(list)
    for path in args.music_dir.iterdir():
        match = re.match(r'^\[([0-9]+)\] (.+)\.(?:aac|aiff|alac|flac|m4a|mp3|oga|ogg|opus|wav|wma)$',
                         path.name, re.IGNORECASE)
        if match and path.is_file() and path.stat().st_size:
            stored_ids.add(match[1])
            local_by_title[normalize(match[2])].append(path)
    ids = dict.fromkeys(re.findall(r'^[0-9]+$', args.track_ids.read_text(), flags=re.MULTILINE))
    missing = [track_id for track_id in ids if track_id not in stored_ids]
    if args.archive.exists():
        archived_ids = set(re.findall(r'^soundcloud ([0-9]+)$', args.archive.read_text(), flags=re.MULTILINE))
    else:
        archived_ids = set()
    print(f'--- Поиск альтернативного аудио для {len(missing)} треков ---', flush=True)
    added = 0
    with TemporaryDirectory(prefix='.sync-audio-', dir=args.music_dir) as tmp, \
            ThreadPoolExecutor(max_workers=4) as executor, args.archive.open('a') as archive:
        for track_id in ids.keys() & (stored_ids - archived_ids):
            archive.write(f'soundcloud {track_id}\n')
        jobs = [executor.submit(recover, track_id, args.music_dir, Path(tmp), local_by_title)
                for track_id in missing]
        for track_id, job in zip(missing, jobs):
            source, title = job.result()
            if source:
                if track_id not in archived_ids:
                    archive.write(f'soundcloud {track_id}\n')
                    archive.flush()
                added += 1
                print(f'  + {track_id} {title} ({source})', flush=True)
            else:
                print(f'  ! {track_id} {title}', flush=True)
    print(f'--- Альтернативные источники: добавлено {added}, осталось {len(missing) - added} ---', flush=True)


if __name__ == '__main__':
    main()
