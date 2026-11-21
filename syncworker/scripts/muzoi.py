"""Search the public Muzoi track catalog for downloadable MP3 files."""

import re
from collections.abc import Iterable
from html.parser import HTMLParser
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


BASE_URL = 'https://muzoi.net'
MAX_PAGE_BYTES = 512 * 1024
MAX_RESULTS = 15
TRACK_PATH = re.compile(r'/uploads/music/\d{4}/\d{2}/[A-Za-z0-9_][A-Za-z0-9_.-]*\.mp3')


class SearchResults(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results_depth = 0
        self.tracks = {}

    def handle_starttag(self, tag, attrs):
        if tag != 'div':
            return
        attrs = dict(attrs)
        if attrs.get('id') == 'dle-content':
            self.results_depth = 1
            return
        if not self.results_depth:
            return
        self.results_depth += 1

        classes = (attrs.get('class') or '').split()
        if 'js-trc' not in classes or len(self.tracks) >= MAX_RESULTS:
            return

        path = attrs.get('data-src') or ''
        artist = (attrs.get('data-subtitle') or '').strip()
        title = (attrs.get('data-title') or '').strip()
        if TRACK_PATH.fullmatch(path) and artist and title:
            self.tracks.setdefault(BASE_URL + path, (artist, title))

    def handle_endtag(self, tag):
        if tag == 'div' and self.results_depth:
            self.results_depth -= 1


def find_candidates(artist: str, title: str) -> Iterable[tuple[str, str, str]]:
    params = urlencode({'do': 'search', 'subaction': 'search', 'story': f'{artist} {title}'})
    request = Request(f'{BASE_URL}/index.php?{params}', headers={'User-Agent': 'musicserver'})
    with urlopen(request, timeout=8) as response:
        final_url = urlsplit(response.geturl())
        if final_url.scheme != 'https' or final_url.netloc != 'muzoi.net':
            return
        page = response.read(MAX_PAGE_BYTES + 1)
        if len(page) > MAX_PAGE_BYTES:
            return

    results = SearchResults()
    results.feed(page.decode('utf-8', errors='replace'))
    for url, (candidate_artist, candidate_title) in results.tracks.items():
        yield url, candidate_artist, candidate_title
