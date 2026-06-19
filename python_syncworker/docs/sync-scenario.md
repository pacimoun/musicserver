<h1 style="color:red">INDEV</h1>

# сценарий синка с soundcloud

взаимодействие с внешними сервисами, только через клиенты
nd_client.sh - клиент navidrome
sc_client.sh - клиент soundcloud
fs_client.sh - клиент файловой системы

config.sh - глобальные настройки и константы

get_sc_data.sh - скачивание и сохранение необходимых данных soundcloud
update_local_storage.sh - актуализация локального хранилища, удаление unliked треков и удаление их айди из archive.txt(кэш скачивания yt-dlp)
sync_sc_likes.sh - синхронизация лайкнутых треков: удаление всех лайков, затем проставление лайков в соответствии с данными полученными в get_sc_data.sh
sync_sc_playlists.sh - синхронизация лайкнутых плейлистов: удалениие существующих .m3u файлов, затем в цикле для каждого плейлиста создаем новый файл и добавляем пути к файлам треков, лайкнутые плейлисты и айди треков из них получены в get_sc_data.sh

full_sync.sh - скрипт вызывающий все остальные в правильной последовательности

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