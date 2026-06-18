<h1 style="color:red">INDEV</h1>

# сценарий синка с soundcloud

### needed soundcloud data:
* sc tracks
* sc liked tracks metadata: id, url, title
* sc playlists metadata: id, url, title
* sc playlists tracklist ids

```mermaid
flowchart TD
    start(((start full sync))) --> ytdlp
    subgraph update local storage
        ytdlp(download tracks from soundcloud) --> get-tracks-info
        get-tracks-info(get actual tracks soundcloud ids) --> remove-old(remove unliked tracks)
    end
    remove-old --> scan(rescan navidrome)
    scan --> get-tracks-info2
    subgraph sync soundcloud likes
        get-tracks-info2(get liked tracks soundcloud ids) --> remove-likes
        remove-likes(remove all likes in navidrome) --> likes(like actual tracks that are not playlists)
    end
    likes --> get-playlists-info
    subgraph sync soundcloud playlists
        get-playlists-info(get liked soundcloud playlists) --> remove-playlists
        remove-playlists(remove playlist files) --> create-playlist
        create-playlist(create playlist files) --> get-playlist-tracks
        get-playlist-tracks(get playlists track soundcloud ids) --> write-playlists(write file paths to playlist files)
    end
    write-playlists --> scan2(rescan navidrome)
```