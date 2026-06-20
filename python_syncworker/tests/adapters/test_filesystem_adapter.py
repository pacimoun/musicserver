from __future__ import annotations

from pathlib import Path

import pytest

from syncworker.adapters.filesystem_adapter import FilesystemAdapter
from syncworker.adapters.models.filesystem_models import LocalTrack


def create_adapter(tmp_path: Path) -> FilesystemAdapter:
    music_dir = tmp_path / "music"
    return FilesystemAdapter(
        music_dir=music_dir,
        playlists_dir=music_dir / "playlists",
        archive_file=music_dir / "archive.txt",
    )


def test_list_tracks_returns_empty_tuple_when_music_dir_does_not_exist(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)

    assert adapter.list_tracks() == ()


def test_list_tracks_returns_only_files_with_soundcloud_id(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)
    adapter.music_dir.mkdir()

    first_track = adapter.music_dir / "[111] first.mp3"
    second_track = adapter.music_dir / "artist - [222] second.flac"
    ignored_without_id = adapter.music_dir / "track-without-id.mp3"
    ignored_directory = adapter.music_dir / "[333] directory"
    playlists_directory = adapter.playlists_dir

    first_track.write_text("first", encoding="utf-8")
    second_track.write_text("second", encoding="utf-8")
    ignored_without_id.write_text("ignored", encoding="utf-8")
    ignored_directory.mkdir()
    playlists_directory.mkdir()

    tracks_by_id = {track.soundcloud_id: track for track in adapter.list_tracks()}

    assert tracks_by_id == {
        "111": LocalTrack(soundcloud_id="111", path=first_track),
        "222": LocalTrack(soundcloud_id="222", path=second_track),
    }


def test_read_archive_returns_empty_tuple_when_archive_file_does_not_exist(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)

    assert adapter.read_archive() == ()


def test_read_archive_returns_only_valid_archive_entries(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)
    adapter.archive_file.parent.mkdir(parents=True)
    adapter.archive_file.write_text(
        "\n".join(
            (
                "soundcloud 111",
                "",
                "invalid-line-without-id",
                "soundcloud 222",
                "  soundcloud 333  ",
            )
        ),
        encoding="utf-8",
    )

    entries = adapter.read_archive()

    assert tuple(entry.item_id for entry in entries) == ("111", "222", "333")
    assert tuple(entry.extractor for entry in entries) == ("soundcloud", "soundcloud", "soundcloud")
    assert tuple(entry.raw for entry in entries) == ("soundcloud 111", "soundcloud 222", "soundcloud 333")


def test_remove_archive_entries_removes_only_matching_valid_entries(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)
    adapter.archive_file.parent.mkdir(parents=True)
    adapter.archive_file.write_text(
        "\n".join(
            (
                "soundcloud 111",
                "soundcloud 222",
                "invalid-line-without-id",
                "soundcloud 333",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    adapter.remove_archive_entries({"222", "missing"})

    assert adapter.archive_file.read_text(encoding="utf-8") == (
        "soundcloud 111\n"
        "invalid-line-without-id\n"
        "soundcloud 333\n"
    )


def test_remove_archive_entries_does_not_create_archive_file_when_it_does_not_exist(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)

    adapter.remove_archive_entries({"111"})

    assert not adapter.archive_file.exists()


def test_remove_archive_entries_does_not_change_archive_file_when_item_ids_are_empty(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)
    adapter.archive_file.parent.mkdir(parents=True)
    adapter.archive_file.write_text("soundcloud 111\n", encoding="utf-8")

    adapter.remove_archive_entries(set())

    assert adapter.archive_file.read_text(encoding="utf-8") == "soundcloud 111\n"


def test_delete_m3u_playlists_clears_entire_playlists_dir(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)
    adapter.playlists_dir.mkdir(parents=True)

    first_playlist = adapter.playlists_dir / "first.m3u"
    second_playlist = adapter.playlists_dir / "second.m3u"
    playlist_like_file = adapter.playlists_dir / "playlist.m3u8"
    smart_playlist = adapter.playlists_dir / "favorites.nsp"
    nested_dir = adapter.playlists_dir / "nested"
    nested_playlist = nested_dir / "nested.m3u"
    music_file = adapter.music_dir / "[111] first.mp3"

    first_playlist.write_text("first", encoding="utf-8")
    second_playlist.write_text("second", encoding="utf-8")
    playlist_like_file.write_text("playlist-like", encoding="utf-8")
    smart_playlist.write_text("smart playlist", encoding="utf-8")
    nested_dir.mkdir()
    nested_playlist.write_text("nested", encoding="utf-8")
    music_file.write_text("track", encoding="utf-8")

    adapter.delete_m3u_playlists()

    assert adapter.playlists_dir.exists()
    assert tuple(adapter.playlists_dir.iterdir()) == ()
    assert music_file.exists()


def test_delete_m3u_playlists_does_nothing_when_playlists_dir_does_not_exist(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)

    adapter.delete_m3u_playlists()

    assert not adapter.playlists_dir.exists()


def test_write_m3u_playlist_creates_playlist_file_with_relative_track_paths(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)

    playlist_file = adapter.write_m3u_playlist(
        title="..bad/name?<> ",
        track_paths=("[111] first.mp3", "[222] second.flac"),
    )

    assert playlist_file == adapter.playlists_dir / "badname.m3u"
    assert playlist_file.read_text(encoding="utf-8") == (
        "#EXTM3U\n"
        "../[111] first.mp3\n"
        "../[222] second.flac\n"
    )


def test_delete_track_removes_existing_track_file(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)
    adapter.music_dir.mkdir()
    track_file = adapter.music_dir / "[111] first.mp3"
    track_file.write_text("track", encoding="utf-8")
    track = LocalTrack(soundcloud_id="111", path=track_file)

    FilesystemAdapter.delete_track(track)

    assert not track_file.exists()


def test_delete_track_does_not_fail_when_track_file_does_not_exist(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)
    track_file = adapter.music_dir / "[111] first.mp3"
    track = LocalTrack(soundcloud_id="111", path=track_file)

    FilesystemAdapter.delete_track(track)

    assert not track_file.exists()


@pytest.mark.parametrize(
    ("title", "expected_filename"),
    (
        ("Playlist", "Playlist"),
        ("bad/name?with*chars", "badnamewithchars"),
        ("...---Playlist", "Playlist"),
        (" /\\?%*:|\"<> ", "unnamed_playlist"),
    ),
)
def test_sanitize_playlist_filename(title: str, expected_filename: str) -> None:
    assert FilesystemAdapter.sanitize_playlist_filename(title) == expected_filename


@pytest.mark.parametrize(
    ("filename", "expected_soundcloud_id"),
    (
        ("[111] first.mp3", "111"),
        ("artist - [222] second.flac", "222"),
        ("[abc] not numeric.mp3", None),
        ("track-without-id.mp3", None),
    ),
)
def test_extract_soundcloud_id(filename: str, expected_soundcloud_id: str | None) -> None:
    assert FilesystemAdapter._extract_soundcloud_id(filename) == expected_soundcloud_id
