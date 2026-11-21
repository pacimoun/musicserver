"""Find public downloads on lmusic.kz."""

from collections.abc import Iterable
from html.parser import HTMLParser
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


BASE_URL = 'https://lmusic.kz'
DOWNLOAD_PATH = re.compile(r'/api/download/[0-9]+')
MAX_PAGE_BYTES = 512 * 1024
MAX_RESULTS = 15


class SearchResults(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tracks = {}

    def handle_starttag(self, tag, attrs):
        if tag != 'div' or len(self.tracks) >= MAX_RESULTS:
            return
        attrs = dict(attrs)
        if 'js-item-mp3' not in (attrs.get('class') or '').split():
            return
        path = attrs.get('data-download_url') or ''
        artist = (attrs.get('data-artist_name') or '').strip()
        title = (attrs.get('data-song_name') or '').strip()
        if DOWNLOAD_PATH.fullmatch(path) and artist and title:
            self.tracks.setdefault(BASE_URL + path, (artist, title))


def find_candidates(artist: str, title: str) -> Iterable[tuple[str, str, str]]:
    query = urlencode({'q': f'{artist} {title}'})
    request = Request(f'{BASE_URL}/search?{query}', headers={'User-Agent': 'musicserver'})
    with urlopen(request, timeout=8) as response:
        final_url = urlsplit(response.geturl())
        if final_url.scheme != 'https' or final_url.netloc != 'lmusic.kz':
            return
        page = response.read(MAX_PAGE_BYTES + 1)
        if len(page) > MAX_PAGE_BYTES:
            return

    results = SearchResults()
    results.feed(page.decode('utf-8', errors='replace'))
    for url, (candidate_artist, candidate_title) in results.tracks.items():
        yield url, candidate_artist, candidate_title
