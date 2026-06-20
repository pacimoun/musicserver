from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, cast

import pytest
import requests

from syncworker.adapters.models.navidrome_models import NavidromeSong, ScanStatus, StarredItems
from syncworker.adapters.navidrome_adapter import NavidromeAdapter


@dataclass(frozen=True)
class RequestCall:
    url: str
    params: list[tuple[str, str]]
    timeout: int


class FakeResponse:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        self.raise_for_status_called = False

    def raise_for_status(self) -> None:
        self.raise_for_status_called = True

    def json(self) -> dict[str, Any]:
        return self.payload


class FakeSession:
    def __init__(self, payloads: tuple[dict[str, Any], ...]):
        self.responses = [FakeResponse(payload) for payload in payloads]
        self.calls: list[RequestCall] = []

    def get(
        self,
        url: str,
        params: list[tuple[str, str]],
        timeout: int,
    ) -> FakeResponse:
        self.calls.append(RequestCall(url=url, params=params, timeout=timeout))
        if not self.responses:
            raise AssertionError(f"Unexpected request: {url}")

        return self.responses.pop(0)


def create_adapter(*payloads: dict[str, Any]) -> tuple[NavidromeAdapter, FakeSession]:
    session = FakeSession(payloads)
    adapter = NavidromeAdapter(
        base_url="http://navidrome:4533/rest/",
        user="user",
        password="password",
        session=cast(requests.Session, cast(object, session)),
    )
    return adapter, session


def navidrome_payload(**response_fields: Any) -> dict[str, Any]:
    response = {"status": "ok"}
    response.update(response_fields)
    return {"subsonic-response": response}


def failed_navidrome_payload(message: str | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {}
    if message is not None:
        error["message"] = message

    return {"subsonic-response": {"status": "failed", "error": error}}


def assert_single_call(session: FakeSession) -> RequestCall:
    assert len(session.calls) == 1
    return session.calls[0]


def assert_auth_params(call: RequestCall) -> None:
    params = dict(call.params)
    salt = params["s"]

    assert params["u"] == "user"
    assert params["t"] == hashlib.md5(f"password{salt}".encode("utf-8")).hexdigest()
    assert params["v"] == "1.16.1"
    assert params["c"] == "syncworker"
    assert params["f"] == "json"
    assert len(salt) == 16
    assert call.timeout == 30


def test_start_scan_sends_start_scan_request() -> None:
    adapter, session = create_adapter(navidrome_payload())

    adapter.start_scan()

    call = assert_single_call(session)
    assert call.url == "http://navidrome:4533/rest/startScan.view"
    assert_auth_params(call)


def test_get_scan_status_maps_scan_status_response() -> None:
    adapter, _ = create_adapter(navidrome_payload(scanStatus={"scanning": True, "count": "7"}))

    assert adapter.get_scan_status() == ScanStatus(scanning=True, count=7)


def test_get_scan_status_returns_none_count_when_count_is_missing_or_invalid() -> None:
    adapter, _ = create_adapter(navidrome_payload(scanStatus={"scanning": False, "count": "invalid"}))

    assert adapter.get_scan_status() == ScanStatus(scanning=False, count=None)


def test_get_starred_maps_song_album_and_artist_ids() -> None:
    adapter, _ = create_adapter(
        navidrome_payload(
            starred={
                "song": [{"id": "song-1"}, {"id": 2}, {"missing_id": "ignored"}],
                "album": {"id": "album-1"},
                "artist": [{"id": "artist-1"}],
            }
        )
    )

    assert adapter.get_starred() == StarredItems(
        song_ids=("song-1", "2"),
        album_ids=("album-1",),
        artist_ids=("artist-1",),
    )


def test_find_song_by_soundcloud_id_returns_exact_matching_song() -> None:
    adapter, session = create_adapter(
        navidrome_payload(
            searchResult3={
                "song": [
                    {
                        "id": "nd-1",
                        "title": "First",
                        "path": "SoundCloud/[111] first.mp3",
                        "artist": "Artist",
                        "album": "Album",
                    },
                    {
                        "id": "nd-2",
                        "title": "Second",
                        "path": "SoundCloud/[222] second.mp3",
                    },
                    {
                        "id": "nd-without-path",
                        "title": "Without path",
                    },
                    {
                        "id": "nd-without-soundcloud-id",
                        "title": "Without SoundCloud id",
                        "path": "SoundCloud/track-without-id.mp3",
                    },
                    "not-a-song",
                ]
            }
        )
    )

    song = adapter.find_song_by_soundcloud_id("111")

    assert song == NavidromeSong(
        id="nd-1",
        title="First",
        soundcloud_id="111",
        path="SoundCloud/[111] first.mp3",
        artist="Artist",
        album="Album",
    )

    call = assert_single_call(session)
    assert call.url == "http://navidrome:4533/rest/search3.view"
    assert ("query", "111") in call.params


def test_find_song_by_soundcloud_id_returns_none_when_exact_song_is_not_found() -> None:
    adapter, _ = create_adapter(
        navidrome_payload(
            searchResult3={
                "song": {
                    "id": "nd-2",
                    "title": "Second",
                    "path": "SoundCloud/[222] second.mp3",
                }
            }
        )
    )

    assert adapter.find_song_by_soundcloud_id("111") is None


def test_find_songs_by_soundcloud_ids_returns_only_found_songs() -> None:
    adapter, _ = create_adapter(
        navidrome_payload(
            searchResult3={
                "song": {
                    "id": "nd-1",
                    "title": "First",
                    "path": "SoundCloud/[111] first.mp3",
                }
            }
        ),
        navidrome_payload(searchResult3={"song": []}),
    )

    assert adapter.find_songs_by_soundcloud_ids(("111", "222")) == (
        NavidromeSong(
            id="nd-1",
            title="First",
            soundcloud_id="111",
            path="SoundCloud/[111] first.mp3",
            artist="",
            album="",
        ),
    )


def test_star_sends_star_request_with_item_id() -> None:
    adapter, session = create_adapter(navidrome_payload())

    adapter.star("song-1")

    call = assert_single_call(session)
    assert call.url == "http://navidrome:4533/rest/star.view"
    assert ("id", "song-1") in call.params
    assert_auth_params(call)


def test_unstar_sends_unstar_request_with_repeated_item_ids() -> None:
    adapter, session = create_adapter(navidrome_payload())

    adapter.unstar(("song-1", "song-2"))

    call = assert_single_call(session)
    assert call.url == "http://navidrome:4533/rest/unstar.view"
    assert call.params[-2:] == [("id", "song-1"), ("id", "song-2")]
    assert_auth_params(call)


def test_unstar_does_not_send_request_when_item_ids_are_empty() -> None:
    adapter, session = create_adapter()

    adapter.unstar(())

    assert session.calls == []


def test_get_raises_runtime_error_when_subsonic_response_is_missing() -> None:
    adapter, _ = create_adapter({"unexpected": "payload"})

    with pytest.raises(RuntimeError, match="missing subsonic-response"):
        adapter.start_scan()


def test_get_raises_runtime_error_when_subsonic_response_has_failed_status() -> None:
    adapter, _ = create_adapter(failed_navidrome_payload("bad credentials"))

    with pytest.raises(RuntimeError, match="Navidrome API error: bad credentials"):
        adapter.start_scan()


def test_map_song_returns_none_when_path_is_missing() -> None:
    assert NavidromeAdapter._map_song({"id": "nd-1", "title": "Track"}) is None


def test_map_song_returns_none_when_path_has_no_soundcloud_id() -> None:
    assert NavidromeAdapter._map_song({"id": "nd-1", "path": "SoundCloud/track.mp3"}) is None


@pytest.mark.parametrize(
    ("path", "expected_soundcloud_id"),
    (
        ("SoundCloud/[111] first.mp3", "111"),
        ("SoundCloud/artist - [222] second.flac", "222"),
        ("SoundCloud/[abc] not numeric.mp3", None),
        ("SoundCloud/track-without-id.mp3", None),
    ),
)
def test_extract_soundcloud_id(path: str, expected_soundcloud_id: str | None) -> None:
    assert NavidromeAdapter._extract_soundcloud_id(path) == expected_soundcloud_id
