from __future__ import annotations

from syncworker.adapters.models.navidrome_models import NavidromeSong
from syncworker.adapters.models.soundcloud_models import SoundCloudLibrary, SoundCloudPlaylist, SoundCloudTrack
from syncworker.adapters.navidrome_adapter import NavidromeAdapter
from syncworker.adapters.soundcloud_adapter import SoundCloudAdapter
from syncworker.models.library_models import LibraryPlaylist, LibraryTrack, MusicLibrary


class LibraryRepository:
    def __init__(
        self,
        soundcloud_adapter: SoundCloudAdapter,
        navidrome_adapter: NavidromeAdapter,
    ):
        self.soundcloud_adapter = soundcloud_adapter
        self.navidrome_adapter = navidrome_adapter

    def get_library(self) -> MusicLibrary:
        soundcloud_library = self.soundcloud_adapter.get_library()
        navidrome_songs = self.navidrome_adapter.find_songs_by_soundcloud_ids(
            tuple(track.id for track in soundcloud_library.all_tracks)
        )

        return self._map_library(
            soundcloud_library=soundcloud_library,
            navidrome_songs=navidrome_songs,
        )

    @staticmethod
    def _map_library(
        soundcloud_library: SoundCloudLibrary,
        navidrome_songs: tuple[NavidromeSong, ...],
    ) -> MusicLibrary:
        return MusicLibrary(
            liked_tracks=LibraryRepository._map_liked_tracks(soundcloud_library.liked_tracks, navidrome_songs),
            playlists=tuple(
                LibraryRepository._map_playlist(playlist, navidrome_songs)
                for playlist in soundcloud_library.playlists
            ),
        )

    @staticmethod
    def _map_liked_tracks(
            soundcloud_liked_tracks: tuple[SoundCloudTrack, ...],
            navidrome_songs: tuple[NavidromeSong, ...]
    ) -> tuple[LibraryTrack, ...]:
        liked_tracks: list[LibraryTrack] = []
        for soundcloud_track in soundcloud_liked_tracks:
            navidrome_song = next(song for song in navidrome_songs if song.soundcloud_id == soundcloud_track.id)
            if navidrome_song is not None:
                liked_tracks.append(
                    LibraryTrack(
                        soundcloud_id=soundcloud_track.id,
                        navidrome_id=navidrome_song.id,
                        soundcloud_url=soundcloud_track.url,
                        title=navidrome_song.title,
                        navidrome_path=navidrome_song.path,
                    )
                )

        return tuple(liked_tracks)

    @staticmethod
    def _map_playlist(
            soundcloud_playlist: SoundCloudPlaylist,
            navidrome_songs: tuple[NavidromeSong, ...]
    ) -> LibraryPlaylist:
        tracks: list[LibraryTrack] = []
        for soundcloud_track in soundcloud_playlist.tracks:
            navidrome_track = next(ns for ns in navidrome_songs if ns.soundcloud_id == soundcloud_track.id)
            if navidrome_track is not None:
                tracks.append(
                    LibraryTrack(
                        soundcloud_id=soundcloud_track.id,
                        navidrome_id=navidrome_track.id,
                        soundcloud_url=soundcloud_track.url,
                        title=navidrome_track.title,
                        navidrome_path=navidrome_track.path,
                    )
                )

        return LibraryPlaylist(
            soundcloud_id=soundcloud_playlist.id,
            soundcloud_url=soundcloud_playlist.url,
            title=soundcloud_playlist.title,
            tracks=tuple(tracks),
        )
