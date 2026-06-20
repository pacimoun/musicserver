from __future__ import annotations

import hashlib
import re
import secrets
from typing import Any

import requests

from syncworker.adapters.models.navidrome_models import NavidromeSong, ScanStatus, StarredItems


SOUNDCLOUD_ID_PATTERN = re.compile(r"\[(?P<id>\d+)]")


class NavidromeAdapter:
    def __init__(
        self,
        base_url: str,
        user: str,
        password: str,
        session: requests.Session | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.user = user
        self.password = password
        self.session = session or requests.Session()

    def start_scan(self) -> None:
        self._get("startScan")

    def get_scan_status(self) -> ScanStatus:
        payload = self._get("getScanStatus")
        scan_status = self._response(payload).get("scanStatus") or {}
        return ScanStatus(
            scanning=bool(scan_status.get("scanning")),
            count=self._optional_int(scan_status.get("count")),
        )

    def get_starred(self) -> StarredItems:
        payload = self._get("getStarred")
        starred = self._response(payload).get("starred") or {}
        return StarredItems(
            song_ids=self._extract_ids(starred.get("song")),
            album_ids=self._extract_ids(starred.get("album")),
            artist_ids=self._extract_ids(starred.get("artist")),
        )

    def find_song_by_soundcloud_id(self, soundcloud_id: str) -> NavidromeSong | None:
        for song in self._search_songs(soundcloud_id):
            if song.soundcloud_id == soundcloud_id:
                return song

        return None

    def find_songs_by_soundcloud_ids(self, soundcloud_ids: tuple[str, ...]) -> tuple[NavidromeSong, ...]:
        songs: list[NavidromeSong] = []

        for soundcloud_id in soundcloud_ids:
            song = self.find_song_by_soundcloud_id(soundcloud_id)
            if song is not None:
                songs.append(song)

        return tuple(songs)

    def star(self, item_id: str) -> None:
        self._get("star", {"id": item_id})

    def unstar(self, item_ids: tuple[str, ...]) -> None:
        if not item_ids:
            return

        self._get("unstar", [("id", item_id) for item_id in item_ids])

    def _search_songs(self, query: str) -> tuple[NavidromeSong, ...]:
        payload = self._get("search3", {"query": query})
        search_result = self._response(payload).get("searchResult3") or {}
        songs = search_result.get("song") or []
        if isinstance(songs, dict):
            songs = [songs]

        navidrome_songs: list[NavidromeSong] = []
        for song in songs:
            if not isinstance(song, dict):
                continue

            navidrome_song = self._map_song(song)
            if navidrome_song is not None:
                navidrome_songs.append(navidrome_song)

        return tuple(navidrome_songs)

    def _get(self, endpoint: str, params: dict[str, str] | list[tuple[str, str]] | None = None) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}/{endpoint}.view",
            params=self._params(params),
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        self._raise_for_subsonic_error(payload)
        return payload

    def _params(
        self,
        params: dict[str, str] | list[tuple[str, str]] | None = None,
    ) -> list[tuple[str, str]]:
        salt = self._salt()
        api_params = [
            ("u", self.user),
            ("t", self._token(salt)),
            ("s", salt),
            ("v", "1.16.1"),
            ("c", "syncworker"),
            ("f", "json"),
        ]

        if params is None:
            return api_params

        if isinstance(params, dict):
            api_params.extend(params.items())
        else:
            api_params.extend(params)

        return api_params

    @staticmethod
    def _salt() -> str:
        return secrets.token_hex(8)

    def _token(self, salt: str) -> str:
        return hashlib.md5(f"{self.password}{salt}".encode("utf-8")).hexdigest()

    @staticmethod
    def _response(payload: dict[str, Any]) -> dict[str, Any]:
        response = payload.get("subsonic-response")
        if not isinstance(response, dict):
            raise RuntimeError("Invalid Navidrome response: missing subsonic-response")

        return response

    @classmethod
    def _raise_for_subsonic_error(cls, payload: dict[str, Any]) -> None:
        response = cls._response(payload)
        if response.get("status") != "failed":
            return

        error = response.get("error") or {}
        message = error.get("message") if isinstance(error, dict) else None
        raise RuntimeError(f"Navidrome API error: {message or 'unknown error'}")

    @staticmethod
    def _extract_ids(items: Any) -> tuple[str, ...]:
        if items is None:
            return ()

        if isinstance(items, dict):
            items = [items]

        if not isinstance(items, list):
            return ()

        return tuple(str(item["id"]) for item in items if isinstance(item, dict) and item.get("id") is not None)

    @staticmethod
    def _map_song(raw_song: dict[str, Any]) -> NavidromeSong | None:
        raw_path = raw_song.get("path")
        if raw_path is None:
            return None

        path = str(raw_path)
        soundcloud_id = NavidromeAdapter._extract_soundcloud_id(path)
        if soundcloud_id is None:
            return None

        return NavidromeSong(
            id=str(raw_song["id"]),
            title=str(raw_song.get("title") or ""),
            soundcloud_id=soundcloud_id,
            path=path,
            artist=str(raw_song.get("artist") or ""),
            album=str(raw_song.get("album") or ""),
        )

    @staticmethod
    def _extract_soundcloud_id(path: str) -> str | None:
        match = SOUNDCLOUD_ID_PATTERN.search(path)
        if match is None:
            return None

        return match.group("id")

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None
