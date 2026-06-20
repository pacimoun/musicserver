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
        navidrome_songs_by_soundcloud_id = {song.soundcloud_id: song for song in navidrome_songs}

        return MusicLibrary(
            liked_tracks=LibraryRepository._map_liked_tracks(
                soundcloud_library.liked_tracks,
                navidrome_songs_by_soundcloud_id,
            ),
            playlists=tuple(
                LibraryRepository._map_playlist(playlist, navidrome_songs_by_soundcloud_id)
                for playlist in soundcloud_library.playlists
            ),
        )

    @staticmethod
    def _map_liked_tracks(
        soundcloud_liked_tracks: tuple[SoundCloudTrack, ...],
        navidrome_songs_by_soundcloud_id: dict[str, NavidromeSong],
    ) -> tuple[LibraryTrack, ...]:
        liked_tracks: list[LibraryTrack] = []
        for soundcloud_track in soundcloud_liked_tracks:
            navidrome_song = navidrome_songs_by_soundcloud_id.get(soundcloud_track.id)
            if navidrome_song is None:
                continue

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
        navidrome_songs_by_soundcloud_id: dict[str, NavidromeSong],
    ) -> LibraryPlaylist:
        tracks: list[LibraryTrack] = []
        for soundcloud_track in soundcloud_playlist.tracks:
            navidrome_track = navidrome_songs_by_soundcloud_id.get(soundcloud_track.id)
            if navidrome_track is None:
                continue

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
