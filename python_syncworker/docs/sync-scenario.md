<h1 style="color:red">INDEV</h1>

# сценарий синка с soundcloud

### needed soundcloud data:
* sc tracks
* sc liked tracks metadata: id, url, title
* sc playlists metadata: id, url, title
* sc playlists tracklist ids

```mermaid
flowchart TD
    start((start full sync))
    download-sc-data(download all soundcloud data: \n tracks \n all tracks data \n liked tracks data \n playlists data \n playlist's tracks data)
    remove-unliked(remove unliked tracks)
    scan(rescan navidrome)
    remove-likes(remove all likes in navidrome)
    likes(like tracks from soundcloud that are not playlists)
    remove-playlists(remove old playlist files)
    create-playlist(create playlist files)
    write-playlists(write file paths to playlist files)
    scan2(rescan navidrome)
    
    start --> download-sc-data
    download-sc-data --> remove-unliked
    subgraph update local storage
        remove-unliked
    end
    remove-unliked --> scan
    scan --> remove-likes
    subgraph sync soundcloud likes
        remove-likes --> likes
    end
    likes --> remove-playlists
    subgraph sync soundcloud playlists
        remove-playlists --> create-playlist
        create-playlist --> write-playlists
    end
    write-playlists --> scan2
```