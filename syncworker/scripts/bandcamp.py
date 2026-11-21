"""Find public audio streams on Bandcamp track pages."""

import json
import re
import unicodedata
from collections.abc import Iterable
from html.parser import HTMLParser
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


SEARCH_URL = "https://bandcamp.com/api/bcsearch_public_api/1/autocomplete_elastic"
PLAYER_URL = "https://bandcamp.com/EmbeddedPlayer"
PAGE_LIMIT = 512 * 1024
# The label's original titles have the same audio as these SoundCloud releases, verified by ISRC previews.
VERIFIED_TRACKS = {
    ("гречка", "девочки любят"): 1760982852,  # Скоростной марафон
    ("гречка", "подружки"): 2117337235,  # Подружки-наркоманки
}


class EmbeddedPlayer(HTMLParser):
    def __init__(self):
        super().__init__()
        self.data = {}

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            player_data = dict(attrs).get("data-player-data")
            if player_data:
                self.data = json.loads(player_data)


def title_key(value):
    normalized = unicodedata.normalize("NFKC", value).casefold().replace("ё", "е")
    return " ".join(re.findall(r"[^\W_]+", normalized))


def public_audio_url(track_id):
    player = EmbeddedPlayer()
    try:
        with urlopen(f"{PLAYER_URL}/track={track_id}/size=small/", timeout=8) as response:
            page = response.read(PAGE_LIMIT + 1)
        if len(page) > PAGE_LIMIT:
            return None
        player.feed(page.decode())
    except (OSError, ValueError):
        return None
    if any(player.data.get(flag) for flag in ("track_private", "album_private", "subscriber_only")):
        return None
    for audio in player.data.get("tracks", []):
        if audio.get("id") != track_id or not audio.get("track_streaming"):
            continue
        url = (audio.get("file") or {}).get("mp3-128") or ""
        media = urlsplit(url)
        if media.scheme == "https" and media.netloc.endswith(".bcbits.com"):
            return url
    return None


def find_candidates(artist: str, title: str) -> Iterable[tuple[str, str, str]]:
    expected_title = title_key(title)
    verified_id = VERIFIED_TRACKS.get((title_key(artist), expected_title))
    if verified_id and (url := public_audio_url(verified_id)):
        yield url, artist, title

    request = Request(SEARCH_URL, data=json.dumps({
        "search_text": f"{artist} {title}",
        "search_filter": "t",
        "fan_id": None,
        "full_page": False,
    }).encode(), headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=8) as response:
        search = json.load(response)

    for track in search.get("auto", {}).get("results", [])[:8]:
        candidate_title = track.get("name") or ""
        candidate_artist = track.get("band_name") or ""
        if track.get("type") != "t" or not candidate_artist or title_key(candidate_title) != expected_title:
            continue

        track_id = track.get("id")
        if not isinstance(track_id, int) or track_id <= 0:
            continue
        if url := public_audio_url(track_id):
            yield url, candidate_artist, candidate_title
