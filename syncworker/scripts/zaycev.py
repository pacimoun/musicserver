"""Find tracks with a public download on Zaycev.net."""

import http.cookiejar
import json
from collections.abc import Iterable
from urllib.error import HTTPError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener


BASE_URL = "https://zaycev.net"
API_URL = f"{BASE_URL}/api/external"
REQUEST_TIMEOUT = 8


def find_candidates(artist: str, title: str) -> Iterable[tuple[str, str, str]]:
    opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def request(path, data=None):
        headers = {"Referer": f"{BASE_URL}/"}
        body = None
        if data is not None:
            headers.update({"Content-Type": "application/json", "Origin": BASE_URL})
            body = json.dumps(data).encode()
        url = f"{API_URL}/{path}"
        with opener.open(Request(url, data=body, headers=headers), timeout=REQUEST_TIMEOUT) as response:
            return response.read()

    primary_artist = artist.partition(",")[0].strip()
    query = urlencode({"q": f"{primary_artist} {title}", "page": 1, "limit": 8})
    search = json.loads(request(f"pages/search/tracks?{query}"))
    tracks = {
        track_id: track
        for track_id, track in search.get("tracksInfo", {}).items()
        if track_id.isdecimal() and track.get("downloadEnabled") is True
    }
    if not tracks:
        return

    files = json.loads(request("track/filezmeta", {
        "trackIds": [int(track_id) for track_id in tracks],
        "subscription": False,
    }))
    for file in files.get("tracks", []):
        track = tracks.get(str(file.get("id")))
        download_key = file.get("download")
        if not track or not isinstance(download_key, str) or not download_key:
            continue
        try:
            url = request(f"track/download/{quote(download_key, safe='')}").decode().strip()
        except HTTPError as error:
            if error.code in (403, 404, 423):
                continue
            raise
        destination = urlsplit(url)
        if destination.scheme == "https" and destination.netloc == "cdndl.zaycev.net":
            yield url, track["artistName"], track["track"]
