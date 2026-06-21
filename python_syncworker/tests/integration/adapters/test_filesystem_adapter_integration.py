from __future__ import annotations

from pathlib import Path

import pytest

from syncworker.adapters.filesystem_adapter import FilesystemAdapter
from syncworker.adapters.models.filesystem_models import LocalTrack

pytestmark = pytest.mark.integration


def create_adapter(tmp_path: Path) -> FilesystemAdapter:
    music_dir = tmp_path / "music"
    return FilesystemAdapter(
        music_dir=music_dir,
        playlists_dir=music_dir / "playlists",
        archive_file=music_dir / "archive.txt",
    )


def test_list_tracks_reads_real_music_directory_without_touching_nested_playlists(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)
    adapter.music_dir.mkdir()
    adapter.playlists_dir.mkdir()

    first_track = adapter.music_dir / "[111] first.mp3"
    second_track = adapter.music_dir / "artist - [222] second.flac"
    file_without_soundcloud_id = adapter.music_dir / "track-without-id.mp3"
    nested_playlist_track = adapter.playlists_dir / "[333] playlist track.mp3"

    first_track.write_text("first", encoding="utf-8")
    second_track.write_text("second", encoding="utf-8")
    file_without_soundcloud_id.write_text("ignored", encoding="utf-8")
    nested_playlist_track.write_text("nested", encoding="utf-8")
    adapter.archive_file.write_text("soundcloud 111\n", encoding="utf-8")

    tracks = adapter.list_tracks()

    assert {track.soundcloud_id: track.path for track in tracks} == {
        "111": first_track,
        "222": second_track,
    }


def test_list_tracks_returns_empty_tuple_when_music_dir_does_not_exist(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)

    assert adapter.list_tracks() == ()


def test_read_archive_returns_empty_tuple_when_archive_file_does_not_exist(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)

    assert adapter.read_archive() == ()


def test_read_archive_and_remove_archive_entries_work_with_real_archive_file(tmp_path: Path) -> None:
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

    assert tuple(entry.item_id for entry in adapter.read_archive()) == ("111", "222", "333")

    adapter.remove_archive_entries({"222", "missing"})

    assert adapter.archive_file.read_text(encoding="utf-8") == (
        "soundcloud 111\n"
        "invalid-line-without-id\n"
        "soundcloud 333\n"
    )
    assert tuple(entry.item_id for entry in adapter.read_archive()) == ("111", "333")


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


def test_write_and_delete_playlists_use_real_playlists_directory_inside_music(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)
    music_track = adapter.music_dir / "[111] first.mp3"
    music_track.parent.mkdir(parents=True)
    music_track.write_text("track", encoding="utf-8")

    playlist_file = adapter.write_m3u_playlist(
        title="..bad/name?<> ",
        track_paths=("[111] first.mp3", "[222] second.flac"),
    )
    extra_file = adapter.playlists_dir / "not-a-playlist.tmp"
    nested_dir = adapter.playlists_dir / "nested"
    nested_file = nested_dir / "nested.m3u"
    extra_file.write_text("extra", encoding="utf-8")
    nested_dir.mkdir()
    nested_file.write_text("nested", encoding="utf-8")

    assert playlist_file == adapter.playlists_dir / "badname.m3u"
    assert playlist_file.read_text(encoding="utf-8") == (
        "#EXTM3U\n"
        "../[111] first.mp3\n"
        "../[222] second.flac\n"
    )

    adapter.delete_m3u_playlists()

    assert adapter.playlists_dir.exists()
    assert tuple(adapter.playlists_dir.iterdir()) == ()
    assert music_track.exists()


def test_delete_m3u_playlists_does_nothing_when_playlists_dir_does_not_exist(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)

    adapter.delete_m3u_playlists()

    assert not adapter.playlists_dir.exists()


def test_delete_track_removes_real_track_file_and_is_idempotent(tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)
    track_file = adapter.music_dir / "[111] first.mp3"
    track_file.parent.mkdir(parents=True)
    track_file.write_text("track", encoding="utf-8")
    track = LocalTrack(soundcloud_id="111", path=track_file)

    adapter.delete_track(track)
    adapter.delete_track(track)

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
def test_write_m3u_playlist_sanitizes_playlist_filename(title: str, expected_filename: str, tmp_path: Path) -> None:
    adapter = create_adapter(tmp_path)

    playlist_file = adapter.write_m3u_playlist(title=title, track_paths=())

    assert playlist_file == adapter.playlists_dir / f"{expected_filename}.m3u"
