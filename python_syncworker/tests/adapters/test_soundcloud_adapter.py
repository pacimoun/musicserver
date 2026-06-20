from __future__ import annotations

from pathlib import Path
from types import TracebackType
from typing import Any, ClassVar

import pytest

from syncworker.adapters import soundcloud_adapter as soundcloud_adapter_module
from syncworker.adapters.models.soundcloud_models import (
    SoundCloudDownloadResult,
    SoundCloudLibrary,
    SoundCloudPlaylist,
    SoundCloudTrack,
)
from syncworker.adapters.soundcloud_adapter import SoundCloudAdapter


class FakeYoutubeDL:
    instances: ClassVar[list[FakeYoutubeDL]] = []
    extract_results: ClassVar[list[Any]] = []
    download_exit_code: ClassVar[int] = 0

    def __init__(self, options: dict[str, Any]):
        self.options = options
        self.download_calls: list[list[str]] = []
        self.extract_calls: list[tuple[str, bool]] = []
        self.entered = False
        self.exited = False
        FakeYoutubeDL.instances.append(self)

    def __enter__(self) -> FakeYoutubeDL:
        self.entered = True
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.exited = True

    def download(self, urls: list[str]) -> int:
        self.download_calls.append(urls)
        return FakeYoutubeDL.download_exit_code

    def extract_info(self, url: str, download: bool) -> Any:
        self.extract_calls.append((url, download))
        if not FakeYoutubeDL.extract_results:
            raise AssertionError(f"Unexpected extract_info call for url: {url}")

        return FakeYoutubeDL.extract_results.pop(0)


@pytest.fixture(autouse=True)
def use_fake_youtube_dl(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeYoutubeDL.instances = []
    FakeYoutubeDL.extract_results = []
    FakeYoutubeDL.download_exit_code = 0
    monkeypatch.setattr(soundcloud_adapter_module, "YoutubeDL", FakeYoutubeDL)


def test_download_tracks_creates_directories_and_calls_youtube_dl_with_expected_options(tmp_path: Path) -> None:
    FakeYoutubeDL.download_exit_code = 17
    adapter = SoundCloudAdapter("https://soundcloud.com/user/likes")
    music_dir = tmp_path / "music"
    archive_file = music_dir / "archive.txt"

    result = adapter.download_tracks(music_dir=music_dir, archive_file=archive_file)

    assert result == SoundCloudDownloadResult(exit_code=17)
    assert music_dir.exists()
    assert archive_file.parent.exists()

    assert len(FakeYoutubeDL.instances) == 1
    youtube_dl = FakeYoutubeDL.instances[0]
    assert youtube_dl.entered
    assert youtube_dl.exited
    assert youtube_dl.download_calls == [["https://soundcloud.com/user/likes"]]
    assert youtube_dl.options == {
        "ignoreerrors": True,
        "download_archive": str(archive_file),
        "format": "bestaudio/best",
        "outtmpl": str(music_dir / "[%(id)s] %(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredquality": "0",
            },
            {"key": "FFmpegMetadata"},
            {"key": "EmbedThumbnail"},
        ],
        "writethumbnail": True,
    }


def test_get_library_maps_liked_tracks_and_playlists() -> None:
    FakeYoutubeDL.extract_results = [
        {
            "entries": [
                {
                    "id": "liked-1",
                    "url": "https://soundcloud.com/user/liked-1",
                    "title": "Liked Track",
                },
                "not-a-dict",
                {
                    "id": "playlist-1",
                    "url": "https://soundcloud.com/user/sets/playlist-1",
                    "title": "Playlist",
                },
            ]
        },
        {
            "entries": [
                {
                    "id": "playlist-track-1",
                    "url": "https://soundcloud.com/user/playlist-track-1",
                    "title": "Playlist Track",
                },
                {
                    "id": "missing-title",
                    "url": "https://soundcloud.com/user/missing-title",
                },
            ]
        },
    ]
    adapter = SoundCloudAdapter("https://soundcloud.com/user/likes")

    library = adapter.get_library()

    assert library == SoundCloudLibrary(
        liked_tracks=(
            SoundCloudTrack(
                id="liked-1",
                url="https://soundcloud.com/user/liked-1",
                title="Liked Track",
            ),
        ),
        playlists=(
            SoundCloudPlaylist(
                id="playlist-1",
                url="https://soundcloud.com/user/sets/playlist-1",
                title="Playlist",
                tracks=(
                    SoundCloudTrack(
                        id="playlist-track-1",
                        url="https://soundcloud.com/user/playlist-track-1",
                        title="Playlist Track",
                    ),
                ),
            ),
        ),
    )

    assert [instance.options for instance in FakeYoutubeDL.instances] == [
        {"extract_flat": True, "quiet": True, "no_warnings": True},
        {"extract_flat": True, "quiet": True, "no_warnings": True},
    ]
    assert FakeYoutubeDL.instances[0].extract_calls == [("https://soundcloud.com/user/likes", False)]
    assert FakeYoutubeDL.instances[1].extract_calls == [("https://soundcloud.com/user/sets/playlist-1", False)]


def test_get_library_raises_when_root_entry_has_missing_required_field() -> None:
    FakeYoutubeDL.extract_results = [
        {
            "entries": [
                {
                    "id": "liked-1",
                    "url": "https://soundcloud.com/user/liked-1",
                }
            ]
        }
    ]
    adapter = SoundCloudAdapter("https://soundcloud.com/user/likes")

    with pytest.raises(RuntimeError, match="SoundCloud entry has no title"):
        adapter.get_library()


def test_get_playlist_tracks_returns_only_entries_with_required_fields() -> None:
    FakeYoutubeDL.extract_results = [
        {
            "entries": [
                {
                    "id": "track-1",
                    "url": "https://soundcloud.com/user/track-1",
                    "title": "Track 1",
                },
                {
                    "id": "missing-url",
                    "title": "Missing URL",
                },
                {
                    "url": "https://soundcloud.com/user/missing-id",
                    "title": "Missing ID",
                },
                {
                    "id": "missing-title",
                    "url": "https://soundcloud.com/user/missing-title",
                },
                "not-a-dict",
            ]
        }
    ]
    adapter = SoundCloudAdapter("https://soundcloud.com/user/likes")

    assert adapter._get_playlist_tracks("https://soundcloud.com/user/sets/playlist") == (
        SoundCloudTrack(
            id="track-1",
            url="https://soundcloud.com/user/track-1",
            title="Track 1",
        ),
    )


def test_extract_flat_returns_youtube_dl_dict_response() -> None:
    FakeYoutubeDL.extract_results = [{"entries": []}]

    result = SoundCloudAdapter._extract_flat("https://soundcloud.com/user/likes")

    assert result == {"entries": []}
    assert len(FakeYoutubeDL.instances) == 1
    youtube_dl = FakeYoutubeDL.instances[0]
    assert youtube_dl.options == {"extract_flat": True, "quiet": True, "no_warnings": True}
    assert youtube_dl.extract_calls == [("https://soundcloud.com/user/likes", False)]
    assert youtube_dl.entered
    assert youtube_dl.exited


def test_extract_flat_raises_when_youtube_dl_result_is_not_dict() -> None:
    FakeYoutubeDL.extract_results = ["invalid-response"]

    with pytest.raises(RuntimeError, match="Invalid SoundCloud response for url"):
        SoundCloudAdapter._extract_flat("https://soundcloud.com/user/likes")


def test_entries_returns_only_dict_entries() -> None:
    assert SoundCloudAdapter._entries(
        {
            "entries": [
                {"id": "track-1"},
                "not-a-dict",
                {"id": "track-2"},
            ]
        }
    ) == ({"id": "track-1"}, {"id": "track-2"})


@pytest.mark.parametrize(
    "result",
    (
        {},
        {"entries": None},
        {"entries": "not-a-list"},
    ),
)
def test_entries_returns_empty_tuple_when_entries_are_missing_or_invalid(result: dict[str, Any]) -> None:
    assert SoundCloudAdapter._entries(result) == ()


@pytest.mark.parametrize(
    ("url", "expected_result"),
    (
        ("https://soundcloud.com/user/sets/playlist", True),
        ("https://soundcloud.com/user/track", False),
    ),
)
def test_is_playlist(url: str, expected_result: bool) -> None:
    assert SoundCloudAdapter._is_playlist(url) is expected_result


def test_required_str_returns_string_value() -> None:
    assert SoundCloudAdapter._required_str({"id": 123}, "id") == "123"


def test_required_str_raises_when_field_is_missing() -> None:
    with pytest.raises(RuntimeError, match="SoundCloud entry has no id"):
        SoundCloudAdapter._required_str({"title": "Track"}, "id")
